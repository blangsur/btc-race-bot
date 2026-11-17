# btc-race-bot

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/blangsur/btc-race-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/blangsur/btc-race-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A long-only cbBTC/USDC paper-trading bot for make.fun's "Race a BTC trading bot live for 24 hours" bounty. It buys dips at least 60 bps below the 180-minute EMA when short-term momentum is negative, and exits on a +80 bps target, a 250 bps trailing stop, a 300 bps hard stop, a 480-bar timeout, or a regime break. Designed for low turnover and robust behaviour on unseen market windows. Dev-window net PnL: +9.76 USDC (4 trades, reproducible byte for byte); all ±20% parameter perturbations stayed profitable.

## Run it

```sh
python3 main.py
```

The bot reads minute bars from the make.fun harness protocol (see `protocol.schema.json` in the competition kit) and writes its actions to stdout; no network calls, no randomness, no wall-clock decisions.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
