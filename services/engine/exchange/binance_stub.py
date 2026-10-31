"""Binance spot client stub — LIVE path placeholder (ccxt-ready)."""
from __future__ import annotations
from typing import List, Optional


class BinanceSpotClient:
    """Stub: validates keys present; real ccxt wiring is v0.2."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        whitelist_ips: str = "",
    ):
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.testnet = testnet
        self.whitelist_ips = self._parse_ips(whitelist_ips)

    @staticmethod
    def _parse_ips(raw: str) -> List[str]:
        return [p.strip() for p in (raw or "").split(",") if p.strip()]

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def set_whitelist(self, raw: str):
        self.whitelist_ips = self._parse_ips(raw)

    def status(self) -> dict:
        return {
            "configured": self.configured,
            "testnet": self.testnet,
            "ready": False,
            "whitelistIps": list(self.whitelist_ips),
            "note": "LIVE trading stub — set MODE=live + keys; full ccxt spot in v0.2. Use paper mode for MVP. Restrict API key to whitelist IPs in Binance API Management.",
        }

    def place_order(self, *args, **kwargs) -> dict:
        if not self.configured:
            return {"ok": False, "error": "BINANCE_API_KEY/SECRET missing"}
        return {
            "ok": False,
            "error": "LIVE Binance execution not enabled in v0.1 — use MODE=paper",
        }
