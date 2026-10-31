"""WinCi trading engine — FastAPI + SSE ticks + paper exchange + DeepSeek plug-in."""
from __future__ import annotations
import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from config import get_settings
from exchange.paper import PaperExchange, SYMBOLS
from exchange.binance_stub import BinanceSpotClient
from signals.registry import evaluate_all, consensus
from bots.momentum import MomentumBot, BotConfig
from ai.deepseek import DeepSeekClient

settings = get_settings()
paper = PaperExchange(
    starting_usdt=settings.PAPER_STARTING_USDT,
    min_notional=settings.MIN_NOTIONAL_USD,
    max_position=settings.MAX_POSITION_USD,
    daily_loss=settings.DAILY_LOSS_LIMIT_USD,
)
binance = BinanceSpotClient(
    settings.BINANCE_API_KEY, settings.BINANCE_API_SECRET, settings.BINANCE_TESTNET
)
deepseek = DeepSeekClient(api_key=getattr(settings, "DEEPSEEK_API_KEY", "") or "")
bot = MomentumBot(paper)
_latest: dict = {}


class OrderIn(BaseModel):
    symbol: str = "BTCUSDT"
    side: str = Field(..., pattern="^(buy|sell)$")
    quantity: float = Field(..., gt=0)
    price: Optional[float] = None
    type: str = "market"


class BotUpdate(BaseModel):
    enabled: Optional[bool] = None
    symbol: Optional[str] = None
    buy_threshold: Optional[float] = None
    sell_threshold: Optional[float] = None
    order_notional_usd: Optional[float] = None
    cooldown_sec: Optional[float] = None


class ModeIn(BaseModel):
    mode: str  # paper | live


class DeepSeekKeyIn(BaseModel):
    api_key: str = ""


class CommentaryIn(BaseModel):
    symbol: str = "BTCUSDT"
    include_boost: bool = False


def _refresh_snapshot(symbol: str = "BTCUSDT") -> dict:
    now = time.time()
    markets = paper.tick_prices(now)
    results = evaluate_all(symbol, now)
    cons = consensus(results)
    boost = deepseek._last_boost if deepseek.configured else 0.0
    adj = round(cons["score"] + boost, 2)
    cons_adj = {**cons, "score": adj, "aiBoost": boost, "rawScore": cons["score"]}
    if adj >= 25:
        cons_adj["action"] = "buy"
    elif adj <= -25:
        cons_adj["action"] = "sell"
    else:
        cons_adj["action"] = "hold"
    snap = {
        "ts": now,
        "mode": settings.MODE,
        "markets": list(markets.values()),
        "symbol": symbol,
        "price": markets.get(symbol, {}).get("price"),
        "signals": [r.__dict__ for r in results],
        "consensus": cons_adj,
        "portfolio": paper.portfolio(),
        "bot": bot.status(),
        "binance": binance.status(),
        "deepseek": deepseek.status(),
    }
    global _latest
    _latest = snap
    return snap


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def loop():
        while True:
            try:
                snap = _refresh_snapshot(bot.cfg.symbol)
                if bot.cfg.enabled:
                    bot.tick(snap["consensus"]["score"])
            except Exception:
                pass
            await asyncio.sleep(2.0)

    task = asyncio.create_task(loop())
    yield
    task.cancel()


app = FastAPI(title="WinCi Engine", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "app": "WinCi", "version": "0.1.0", "mode": settings.MODE}


@app.get("/api/status")
def api_status():
    return {
        "mode": settings.MODE,
        "isLive": settings.is_live,
        "minNotionalUsd": settings.MIN_NOTIONAL_USD,
        "maxPositionUsd": settings.MAX_POSITION_USD,
        "dailyLossLimitUsd": settings.DAILY_LOSS_LIMIT_USD,
        "binance": binance.status(),
        "deepseek": {
            "configured": deepseek.configured,
            "baseUrl": "https://api.deepseek.com",
            "model": deepseek.model,
        },
        "symbols": SYMBOLS,
    }


@app.get("/api/markets")
def api_markets():
    return list(paper.tick_prices().values())


@app.get("/api/signals")
def api_signals(symbol: str = Query("BTCUSDT")):
    now = time.time()
    results = evaluate_all(symbol, now)
    cons = consensus(results)
    return {
        "symbol": symbol,
        "ts": now,
        "consensus": cons,
        "signals": [r.__dict__ for r in results],
        "count": len(results),
    }


@app.get("/api/portfolio")
def api_portfolio():
    return paper.portfolio()


@app.get("/api/orders")
def api_orders():
    return {"orders": paper.recent_orders(), "fills": paper.recent_fills()}


@app.post("/api/order")
def api_order(body: OrderIn):
    if settings.is_live:
        # v0.1: refuse live; keep paper safe
        live = binance.place_order(body.symbol, body.side, body.quantity, body.price)
        if not live.get("ok"):
            raise HTTPException(400, live.get("error", "live unavailable"))
        return live
    result = paper.place_order(
        body.symbol, body.side, body.quantity, body.price, body.type
    )
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "order failed"))
    return result


@app.get("/api/bots")
def api_bots():
    return {"bots": [bot.status()]}


@app.patch("/api/bots/{bot_id}")
def api_bot_update(bot_id: str, body: BotUpdate):
    if bot_id != bot.cfg.id:
        raise HTTPException(404, "bot not found")
    data = body.model_dump(exclude_none=True)
    if "enabled" in data:
        bot.set_enabled(bool(data.pop("enabled")))
    if data:
        bot.update(**data)
    return bot.status()


@app.post("/api/kill-switch/reset")
def api_kill_reset():
    paper.reset_kill()
    return {"ok": True, "portfolio": paper.portfolio()}


@app.post("/api/settings/mode")
def api_mode(body: ModeIn):
    mode = body.mode.lower()
    if mode not in ("paper", "live"):
        raise HTTPException(400, "mode must be paper|live")
    if mode == "live" and not binance.configured:
        raise HTTPException(400, "BINANCE_API_KEY/SECRET required for live")
    settings.MODE = mode
    return {"ok": True, "mode": settings.MODE, "note": "live execution stub in v0.1"}


@app.get("/api/deepseek/status")
def api_deepseek_status():
    return deepseek.status()


@app.post("/api/deepseek/key")
def api_deepseek_key(body: DeepSeekKeyIn):
    """Runtime key for session only — prefer .env DEEPSEEK_API_KEY. Never logged."""
    deepseek.set_api_key(body.api_key)
    return {"ok": True, "configured": deepseek.configured}


@app.post("/api/deepseek/commentary")
async def api_deepseek_commentary(body: CommentaryIn):
    snap = _refresh_snapshot(body.symbol)
    signals = sorted(snap["signals"], key=lambda s: abs(s["score"]), reverse=True)
    boost = 0.0
    if body.include_boost:
        boost = await deepseek.signal_boost(body.symbol, snap["consensus"]["rawScore"])
    commentary = await deepseek.short_trade_commentary(
        body.symbol,
        snap["price"] or 0,
        snap["consensus"],
        signals,
    )
    return {
        "commentary": commentary,
        "aiBoost": boost,
        "consensus": snap["consensus"],
    }


@app.get("/api/sse/ticks")
async def sse_ticks(symbol: str = Query("BTCUSDT")):
    async def gen():
        while True:
            snap = _refresh_snapshot(symbol)
            # trim signals for wire size — full list on /api/signals
            payload = {
                "ts": snap["ts"],
                "mode": snap["mode"],
                "symbol": symbol,
                "price": snap["price"],
                "markets": snap["markets"],
                "consensus": snap["consensus"],
                "portfolio": snap["portfolio"],
                "bot": snap["bot"],
                "signalSample": snap["signals"][:12],
                "signalCount": len(snap["signals"]),
                "deepseekConfigured": deepseek.configured,
            }
            yield {"event": "tick", "data": json.dumps(payload)}
            await asyncio.sleep(2.0)

    return EventSourceResponse(gen())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.ENGINE_HOST,
        port=settings.ENGINE_PORT,
        reload=False,
    )
