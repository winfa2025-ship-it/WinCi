"""Binance spot client stub — LIVE path placeholder (ccxt-ready)."""
from __future__ import annotations
from typing import Optional

class BinanceSpotClient:
    """Stub: validates keys present; real ccxt wiring is v0.2."""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.testnet = testnet

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def status(self) -> dict:
        return {
            "configured": self.configured,
            "testnet": self.testnet,
            "ready": False,
            "note": "LIVE trading stub — set MODE=live + keys; full ccxt spot in v0.2. Use paper mode for MVP.",
        }

    def place_order(self, *args, **kwargs) -> dict:
        if not self.configured:
            return {"ok": False, "error": "BINANCE_API_KEY/SECRET missing"}
        return {
            "ok": False,
            "error": "LIVE Binance execution not enabled in v0.1 — use MODE=paper",
        }
