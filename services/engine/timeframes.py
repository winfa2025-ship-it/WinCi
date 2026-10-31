"""Short-trade timeframes: 1m / 5m / 15m."""
from __future__ import annotations
import hashlib
import math
import time
from typing import Dict, List, Literal

Timeframe = Literal["1m", "5m", "15m"]

TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m")
TF_SECONDS: Dict[str, int] = {"1m": 60, "5m": 300, "15m": 900}
DEFAULT_TF: Timeframe = "1m"


def normalize_tf(value: str | None) -> str:
    v = (value or DEFAULT_TF).strip().lower()
    if v not in TF_SECONDS:
        raise ValueError(f"timeframe must be one of {', '.join(TIMEFRAMES)}")
    return v


def tf_seconds(tf: str) -> int:
    return TF_SECONDS[normalize_tf(tf)]


def bucket_ts(ts: float, tf: str) -> int:
    sec = tf_seconds(tf)
    return int(ts // sec)


def loop_sleep_sec(tf: str) -> float:
    """Engine poll interval — faster than candle close, still TF-aware."""
    sec = tf_seconds(tf)
    # poll ~1/30 of a bar, clamped 1–5s so UI stays responsive
    return max(1.0, min(5.0, sec / 30.0))


def default_bot_cooldown(tf: str) -> float:
    """Suggest cooldown ≈ one bar so bots don't overtrade inside a candle."""
    return float(tf_seconds(tf))


def candles_stub(
    symbol: str,
    tf: str,
    *,
    count: int = 60,
    now: float | None = None,
    last_price: float | None = None,
) -> List[dict]:
    """Deterministic OHLC stub candles for chart UI (not real exchange data)."""
    tf = normalize_tf(tf)
    sec = tf_seconds(tf)
    now = now or time.time()
    # align to closed bar end
    end_bucket = int(now // sec)
    base = last_price
    if base is None or base <= 0:
        # rough base from hash of symbol
        h0 = int(hashlib.sha256(symbol.encode()).hexdigest()[:6], 16)
        base = 100 + (h0 % 90000) / 10.0
        if "BTC" in symbol:
            base = 68000.0
        elif "ETH" in symbol:
            base = 3500.0

    out: List[dict] = []
    px = base
    for i in range(count, 0, -1):
        bucket = end_bucket - i
        open_ts = bucket * sec
        h = hashlib.sha256(f"{symbol}:{tf}:{bucket}".encode()).hexdigest()
        n1 = (int(h[:6], 16) / 0xFFFFFF - 0.5) * 0.008
        n2 = (int(h[6:12], 16) / 0xFFFFFF - 0.5) * 0.006
        wave = math.sin(bucket * 0.17 + int(h[12:14], 16)) * 0.003
        o = px
        c = max(1e-8, o * (1 + n1 + wave))
        hi = max(o, c) * (1 + abs(n2))
        lo = min(o, c) * (1 - abs(n2) * 0.8)
        vol = round(10 + (int(h[14:20], 16) % 10000) / 10.0, 2)
        decimals = 8 if c < 1 else 2
        out.append(
            {
                "t": open_ts,
                "T": open_ts + sec,
                "o": round(o, decimals),
                "h": round(hi, decimals),
                "l": round(lo, decimals),
                "c": round(c, decimals),
                "v": vol,
                "interval": tf,
                "symbol": symbol,
            }
        )
        px = c
    # nudge last close toward live last_price if provided
    if last_price and out:
        last = out[-1]
        last["c"] = round(float(last_price), 8 if last_price < 1 else 2)
        last["h"] = max(last["h"], last["c"], last["o"])
        last["l"] = min(last["l"], last["c"], last["o"])
    return out
