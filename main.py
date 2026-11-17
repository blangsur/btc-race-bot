import json
import sys
from collections import deque

SYMBOL = "CBBTC"
BPS = 10000
PRICE_SCALE = 5
SLIPPAGE_CAP_BUY = 100
SLIPPAGE_CAP_SELL = 10000

PARAMS = {
    "slow": 240,
    "confirm": 120,
    "dip_span": 180,
    "entry_bps": 8.0,
    "stop_bps": 250.0,
    "hard_stop_bps": 300.0,
    "cooldown": 15,
    "max_hold": 480,
    "dip_bps": 60.0,
    "target_bps": 80.0,
    "regime_drop": 400.0,
    "max_dip_bps": 1000.0,
    "min_vol": 4.0,
}


class Strategy:
    def __init__(self, params=None):
        self.p = dict(PARAMS)
        if params:
            self.p.update(params)
        n = max(self.p["slow"], self.p["confirm"], self.p["dip_span"]) + 2
        self.closes = deque(maxlen=n)
        self.ema_slow = None
        self.ema_confirm = None
        self.ema_dip = None
        self.vol = 0.0
        self.holding = False
        self.pending = None
        self.entry_seq = 0
        self.entry_price = 0.0
        self.peak = 0.0
        self.cooldown_until = 0

    @staticmethod
    def _ema(old, value, span):
        if old is None:
            return value
        a = 2.0 / (span + 1.0)
        return old + a * (value - old)

    def _mom(self, span):
        if len(self.closes) <= span:
            return None
        old = self.closes[-span - 1]
        return (self.closes[-1] / old - 1.0) * BPS if old > 0 else None

    def _update(self, bar):
        price = int(bar["c"]) / 10**PRICE_SCALE
        self.closes.append(price)
        for key, span in (("ema_slow", self.p["slow"]), ("ema_confirm", self.p["confirm"]), ("ema_dip", self.p["dip_span"])):
            old = getattr(self, key)
            if old is None and len(self.closes) >= span:
                setattr(self, key, sum(list(self.closes)[-span:]) / span)
            elif old is not None:
                setattr(self, key, self._ema(old, price, span))
        if len(self.closes) >= 2 and self.closes[-2] > 0:
            ret = abs(price / self.closes[-2] - 1.0) * BPS
            self.vol = self._ema(self.vol, ret, 60)

    def _enter(self):
        p = self.p
        if len(self.closes) < p["confirm"] + 2:
            return False
        if self.ema_slow is None or self.ema_confirm is None or self.ema_dip is None:
            return False
        if self.vol < p["min_vol"]:
            return False
        c = self.closes[-1]
        m_long = self._mom(p["confirm"])
        if m_long is not None and m_long < -p["regime_drop"]:
            return False
        m_short = self._mom(10)
        if m_short is not None and m_short > -p["entry_bps"]:
            return False
        return bool(self.ema_dip * (1.0 - p["max_dip_bps"] / BPS) < c <= self.ema_dip * (1.0 - p["dip_bps"] / BPS))

    def _exit(self, seq, price):
        p = self.p
        if price < self.peak * (1.0 - p["stop_bps"] / BPS):
            return True
        if price < self.entry_price * (1.0 - p["hard_stop_bps"] / BPS):
            return True
        if price >= self.entry_price * (1.0 + p["target_bps"] / BPS):
            return True
        if seq - self.entry_seq >= p["max_hold"]:
            return True
        m_long = self._mom(p["confirm"])
        if m_long is not None and m_long < -p["regime_drop"]:
            return True
        return False

    def decide(self, msg):
        seq = msg["seq"]
        bar = msg["bars"][0]
        self._update(bar)
        price = int(bar["c"]) / 10**PRICE_SCALE

        for fill in msg.get("fills", []):
            cid = str(fill.get("client_id", ""))
            if not cid.startswith("x"):
                continue
            self.pending = None
            if fill.get("status") != "filled":
                continue
            if fill.get("side") == "sell":
                self.holding = False
                self.cooldown_until = seq + self.p["cooldown"]
            else:
                self.holding = True
                self.entry_seq = seq
                self.entry_price = price
                self.peak = price

        positions = msg["account"].get("positions", [])
        qty = int(positions[0]["qty"]) if positions else 0
        if qty == 0 and self.holding:
            self.holding = False
            self.cooldown_until = seq + self.p["cooldown"]
        elif qty > 0 and not self.holding:
            self.holding = True
            self.entry_seq = seq
            self.entry_price = price
            self.peak = price

        if self.holding:
            self.peak = max(self.peak, price)
            if self.pending != "sell" and self._exit(seq, price):
                return [{"side": "sell", "client_id": f"xs{seq}", "symbol": SYMBOL, "qty": str(qty), "max_slippage_bps": SLIPPAGE_CAP_SELL}]
            return []
        if self.pending or seq < self.cooldown_until:
            return []
        if not self._enter():
            return []
        cash = int(msg["account"]["cash_quote_units"])
        if cash < 1_000_000:
            return []
        return [{"side": "buy", "client_id": f"xb{seq}", "symbol": SYMBOL, "notional_quote_units": str(cash), "max_slippage_bps": SLIPPAGE_CAP_BUY}]


def run():
    state = None
    strategy = None
    for line in sys.stdin.buffer:
        if not line.strip():
            continue
        msg = json.loads(line)
        kind = msg.get("type")
        if kind == "hello":
            state = msg
            strategy = Strategy()
        elif kind == "batch":
            orders = strategy.decide(msg) if state else []
            reply = {"type": "reply", "seq": msg["seq"], "orders": orders}
            sys.stdout.write(json.dumps(reply, separators=(",", ":")) + "\n")
            sys.stdout.flush()
        elif kind == "done":
            return


if __name__ == "__main__":
    run()
