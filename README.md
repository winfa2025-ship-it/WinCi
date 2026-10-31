# WinCi

Personal-use crypto **short-trading** dashboard for Hoi (海琋).

- Dark PWA UI: Markets · Chart stub · Order ticket · Bots / **AutoEarn** · **100 signal board** · Portfolio · Settings
- **Email + Google login** (local JWT; Demo Google when `GOOGLE_CLIENT_ID` empty)
- Engine: FastAPI paper exchange + momentum + AutoEarn bots + SSE ticks
- Optional **DeepSeek** AI commentary / signal boost (`https://api.deepseek.com`)
- Optional Binance keys for future LIVE (v0.1.x stub — paper works without keys)
- **Binance IP whitelist** reminder + outbound IP detector
- Min notional **$1 USD** · max position · daily loss kill-switch
- **Connection indicators**: green = linked, red = missing (Auth / Binance / DeepSeek / Bot)
- **Short-trade timeframes**: selectable **1m / 5m / 15m** (chart candles, signal cadence, Momentum / AutoEarn)

> **Not financial advice.** Personal use only. Default **PAPER**. AutoEarn does **not** guarantee profit（唔保證盈利／過去表現唔代表將來）. Never commit `.env` secrets.

中文說明見 [README.zh-Hant.md](./README.zh-Hant.md) · 產品設計 [docs/PRODUCT.md](./docs/PRODUCT.md)

## Quick start

```bash
# 1) Engine
cd services/engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example ../../.env   # optional edits
uvicorn main:app --host 0.0.0.0 --port 8787

# 2) Web (another terminal)
cd apps/web
npm install
npm run dev
# open http://127.0.0.1:5173
```

Or with Docker Compose (engine + static preview after build):

```bash
docker compose up --build
```

## Environment

Copy `.env.example` → `.env`:

| Variable | Meaning |
|----------|---------|
| `MODE` | `paper` (default) or `live` |
| `BINANCE_API_KEY` / `SECRET` | LIVE only; spot trade, **no withdraw** |
| `BINANCE_WHITELIST_IPS` | Comma-separated IPs — **reminder only**; paste the same list into Binance API Management |
| `JWT_SECRET` | HS256 secret for email/Google JWT (change for anything beyond local demo) |
| `GOOGLE_CLIENT_ID` | Google Identity Services client ID; empty → Demo Google login |
| `DEEPSEEK_API_KEY` | Optional AI; paper works without it |
| `MIN_NOTIONAL_USD` | Default `1` |
| `MAX_POSITION_USD` | Default `500` |
| `DAILY_LOSS_LIMIT_USD` | Default `50` |

## Auth

- `POST /auth/register` · `POST /auth/login` · `POST /auth/google` · `GET /auth/me`
- Email/password stored in local SQLite (`data/winci_users.db`, gitignored)
- Google: real ID-token verify when `GOOGLE_CLIENT_ID` is set; otherwise credential `demo` works for personal demo

## Short-trade timeframes

Top bar + Chart / Bots / Signals: pick **1m**, **5m**, or **15m**.

- Engine: `GET/POST /api/timeframe`, `GET /api/candles?timeframe=`
- Signals re-bucket on the selected TF; bots sync cooldown ≈ one bar
- SSE ticks include `timeframe` + recent candle stubs

## AutoEarn

Opt-in bot on the **Bots** tab: position size USD, max daily loss %, kill switch. Extends momentum consensus. **No guaranteed profit.** Default paper.

## Binance API IP whitelist

1. Start the engine, open Settings → **偵測 outbound IP**, or `GET /api/binance/outbound-ip` (alias `/binance/outbound-ip`).
2. In Binance → **API Management** → edit your key → enable **IP access restriction** → paste that IP (and any others).
3. Optionally store the same list in `.env` as `BINANCE_WHITELIST_IPS=1.2.3.4` (comma-separated) as a reminder — WinCi does **not** push this to Binance for you.

## Connection indicators

Header and Settings show status dots:

| Dot | Green | Red |
|-----|-------|-----|
| Auth | Logged in | Guest / logged out |
| Binance | API key+secret set | Missing |
| DeepSeek | API key configured | Missing |
| Bot | Momentum or AutoEarn running | Both stopped |

## 「100 AI」honesty

100 **named signal analyzers** (TA / funding / OI / orderbook / news stubs…) voting into a consensus score — **not** 100 LLM calls per tick. DeepSeek is an **optional** commentary / small boost plug-in.

## MVP vs later

| Now (v0.1.2) | Later |
|--------------|--------|
| Paper simulator + momentum + AutoEarn | Real Binance spot via ccxt |
| Email / Demo Google JWT | Full GIS button when client id set |
| 100 deterministic mock signals | Real indicators / funding / news |
| Chart OHLC stub + 1m/5m/15m | TradingView |
| DeepSeek optional commentary | Richer AI tools |

## Download

- Clone: https://github.com/winfa2025-ship-it/WinCi
- Source zip: GitHub **Release v0.1.2** assets

## Risk note

Crypto trading can lose money quickly. Kill-switch and limits reduce — not eliminate — risk. LIVE mode in v0.1.x refuses real orders until Binance path is completed in v0.2. AutoEarn is **not** a money guarantee.
