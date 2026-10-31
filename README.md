# WinCi

Personal-use crypto **short-trading** dashboard for Hoi (海琋).

- Dark PWA UI: Markets · Chart stub · Order ticket · Bots · **100 signal board** · Portfolio · Settings
- Engine: FastAPI paper exchange + momentum bot + SSE ticks
- Optional **DeepSeek** AI commentary / signal boost (`https://api.deepseek.com`)
- Optional Binance keys for future LIVE (v0.1 stub — paper works without keys)
- Min notional **$1 USD** · max position · daily loss kill-switch

> **Not financial advice.** Personal use only. Default **PAPER**. Never commit `.env` secrets.

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
| `DEEPSEEK_API_KEY` | Optional AI; paper works without it |
| `MIN_NOTIONAL_USD` | Default `1` |
| `MAX_POSITION_USD` | Default `500` |
| `DAILY_LOSS_LIMIT_USD` | Default `50` |

## 「100 AI」honesty

100 **named signal analyzers** (TA / funding / OI / orderbook / news stubs…) voting into a consensus score — **not** 100 LLM calls per tick. DeepSeek is an **optional** commentary / small boost plug-in.

## MVP vs later

| Now (v0.1) | Later |
|------------|--------|
| Paper simulator + demo bot | Real Binance spot via ccxt |
| 100 deterministic mock signals | Real indicators / funding / news |
| Chart sparkline stub | TradingView |
| DeepSeek optional commentary | Richer AI tools |

## Download

- Clone: see GitHub repo URL on the Releases / Code page
- Source zip: GitHub **Release v0.1.0** assets

## Risk note

Crypto trading can lose money quickly. Kill-switch and limits reduce — not eliminate — risk. LIVE mode in v0.1 refuses real orders until Binance path is completed in v0.2.
