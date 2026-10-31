"""WinCi trading engine — FastAPI + SSE + paper + auth + AutoEarn + DeepSeek."""
from __future__ import annotations
import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from config import get_settings
from exchange.paper import PaperExchange, SYMBOLS
from exchange.binance_stub import BinanceSpotClient
from signals.registry import evaluate_all, consensus
from bots.momentum import MomentumBot
from bots.autoearn import AutoEarnBot, DISCLAIMER_ZH, DISCLAIMER_EN
from ai.deepseek import DeepSeekClient
from auth.router import router as auth_router

APP_VERSION = "0.1.1"

settings = get_settings()
paper = PaperExchange(
    starting_usdt=settings.PAPER_STARTING_USDT,
    min_notional=settings.MIN_NOTIONAL_USD,
    max_position=settings.MAX_POSITION_USD,
    daily_loss=settings.DAILY_LOSS_LIMIT_USD,
)
binance = BinanceSpotClient(
    settings.BINANCE_API_KEY,
    settings.BINANCE_API_SECRET,
    settings.BINANCE_TESTNET,
    getattr(settings, "BINANCE_WHITELIST_IPS", "") or "",
)
deepseek = DeepSeekClient(api_key=getattr(settings, "DEEPSEEK_API_KEY", "") or "")
bot = MomentumBot(paper)
autoearn = AutoEarnBot(paper)
_latest: dict = {}
_cached_outbound_ip: dict = {"ip": None, "checkedAt": None, "error": None}


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
    position_size_usd: Optional[float] = None
    cooldown_sec: Optional[float] = None
    max_daily_loss_pct: Optional[float] = None
    kill_switch: Optional[bool] = None


class ModeIn(BaseModel):
    mode: str  # paper | live


class DeepSeekKeyIn(BaseModel):
    api_key: str = ""


class CommentaryIn(BaseModel):
    symbol: str = "BTCUSDT"
    include_boost: bool = False


class WhitelistIn(BaseModel):
    ips: str = ""  # comma-separated


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
        "autoearn": autoearn.status(),
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
                snap = _refresh_snapshot(bot.cfg.symbol if bot.cfg.enabled else autoearn.cfg.symbol)
                score = snap["consensus"]["score"]
                if bot.cfg.enabled:
                    bot.tick(score)
                if autoearn.cfg.enabled:
                    autoearn.tick(score)
            except Exception:
                pass
            await asyncio.sleep(2.0)

    task = asyncio.create_task(loop())
    yield
    task.cancel()


app = FastAPI(title="WinCi Engine", version=APP_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"ok": True, "app": "WinCi", "version": APP_VERSION, "mode": settings.MODE}


@app.get("/api/status")
def api_status():
    return {
        "version": APP_VERSION,
        "mode": settings.MODE,
        "isLive": settings.is_live,
        "minNotionalUsd": settings.MIN_NOTIONAL_USD,
        "maxPositionUsd": settings.MAX_POSITION_USD,
        "dailyLossLimitUsd": settings.DAILY_LOSS_LIMIT_USD,
        "binance": binance.status(),
        "binanceWhitelistIps": list(binance.whitelist_ips),
        "googleConfigured": bool(settings.GOOGLE_CLIENT_ID),
        "deepseek": {
            "configured": deepseek.configured,
            "baseUrl": "https://api.deepseek.com",
            "model": deepseek.model,
        },
        "autoearnDisclaimerZh": DISCLAIMER_ZH,
        "autoearnDisclaimerEn": DISCLAIMER_EN,
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
    return {"bots": [bot.status(), autoearn.status()]}


@app.patch("/api/bots/{bot_id}")
def api_bot_update(bot_id: str, body: BotUpdate):
    target = None
    if bot_id == bot.cfg.id:
        target = bot
    elif bot_id == autoearn.cfg.id:
        target = autoearn
    else:
        raise HTTPException(404, "bot not found")
    data = body.model_dump(exclude_none=True)
    if "kill_switch" in data and target is autoearn:
        autoearn.set_kill(bool(data.pop("kill_switch")))
    if "enabled" in data:
        target.set_enabled(bool(data.pop("enabled")))
    if data:
        target.update(**data)
    return target.status()


@app.post("/api/kill-switch/reset")
def api_kill_reset():
    paper.reset_kill()
    autoearn.set_kill(False)
    return {"ok": True, "portfolio": paper.portfolio(), "autoearn": autoearn.status()}


@app.post("/api/settings/mode")
def api_mode(body: ModeIn):
    mode = body.mode.lower()
    if mode not in ("paper", "live"):
        raise HTTPException(400, "mode must be paper|live")
    if mode == "live" and not binance.configured:
        raise HTTPException(400, "BINANCE_API_KEY/SECRET required for live")
    settings.MODE = mode
    return {"ok": True, "mode": settings.MODE, "note": "live execution stub in v0.1.x"}


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


@app.get("/binance/outbound-ip")
@app.get("/api/binance/outbound-ip")
async def binance_outbound_ip():
    """Detect this engine's public outbound IP for Binance API IP whitelist."""
    global _cached_outbound_ip
    ip = None
    err = None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            for url in (
                "https://api.ipify.org?format=json",
                "https://ifconfig.me/ip",
                "https://icanhazip.com",
            ):
                try:
                    r = await client.get(url)
                    if r.status_code != 200:
                        continue
                    text = r.text.strip()
                    if url.endswith("json"):
                        ip = r.json().get("ip")
                    else:
                        ip = text.split()[0] if text else None
                    if ip:
                        break
                except Exception as e:
                    err = str(e)
                    continue
    except Exception as e:
        err = str(e)
    _cached_outbound_ip = {
        "ip": ip,
        "checkedAt": time.time(),
        "error": None if ip else (err or "could not detect outbound IP"),
    }
    return {
        **_cached_outbound_ip,
        "whitelistIps": list(binance.whitelist_ips),
        "hintZh": "將呢個 IP 貼去幣安 API 管理 → IP 存取限制（白名單）。亦可以寫入 .env 嘅 BINANCE_WHITELIST_IPS 做備忘。",
        "hintEn": "Paste this IP into Binance → API Management → IP access restriction. Also store in BINANCE_WHITELIST_IPS as a reminder.",
    }


@app.get("/api/binance/whitelist")
def api_binance_whitelist_get():
    return {
        "ips": list(binance.whitelist_ips),
        "raw": ",".join(binance.whitelist_ips),
        "note": "Reminder list only — enforce the same IPs in Binance API Management UI.",
    }


@app.post("/api/binance/whitelist")
def api_binance_whitelist_set(body: WhitelistIn):
    """Session reminder of IPs; does not change Binance — you must set them in Binance UI."""
    binance.set_whitelist(body.ips)
    settings.BINANCE_WHITELIST_IPS = body.ips
    return {
        "ok": True,
        "ips": list(binance.whitelist_ips),
        "note": "Saved in-process. Persist via .env BINANCE_WHITELIST_IPS. Still paste into Binance API Management.",
    }


@app.get("/api/sse/ticks")
async def sse_ticks(symbol: str = Query("BTCUSDT")):
    async def gen():
        while True:
            snap = _refresh_snapshot(symbol)
            payload = {
                "ts": snap["ts"],
                "mode": snap["mode"],
                "symbol": symbol,
                "price": snap["price"],
                "markets": snap["markets"],
                "consensus": snap["consensus"],
                "portfolio": snap["portfolio"],
                "bot": snap["bot"],
                "autoearn": snap["autoearn"],
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
