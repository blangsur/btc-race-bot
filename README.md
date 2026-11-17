# BTC 24h replay bot

A deterministic, stdlib-only Python 3.13 bot for the make.fun cbBTC/USDC bars-replay race.

`main.py` reads newline-delimited JSON from stdin, answers every `batch` with exactly one `reply`, and exits on `done`. It keeps no files and uses no clock, network, randomness, or environment state.

The strategy is long-only mean reversion. It waits for a 180-minute EMA to form, then buys the full cash balance when price is at least 60 bps below that EMA, 10-minute momentum is down at least 8 bps, 120-minute momentum is above -400 bps, and EMA volatility is at least 4 bps. It sells at +80 bps from entry, a 250 bps stop from the peak, a 300 bps hard stop, after 480 bars, or if 120-minute momentum breaks -400 bps. Orders use deterministic client ids `xb{seq}` and `xs{seq}`.

Local official dev grade: net PnL +9.763316 USDC, 4 trades, 0 rejected orders, max drawdown 0.006605551.

Run with:

```sh
python3 -P -s main.py
```
