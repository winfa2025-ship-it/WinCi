"""DeepSeek chat plug-in — optional commentary + signal boost.

Base URL: https://api.deepseek.com
Paper mode works without DEEPSEEK_API_KEY.
"""
from __future__ import annotations
import time
from typing import Any, Optional
import httpx

DEEPSEEK_BASE = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"

class DeepSeekClient:
    def __init__(self, api_key: str = "", model: str = DEFAULT_MODEL):
        self.api_key = (api_key or "").strip()
        self.model = model
        self._last_commentary: Optional[dict] = None
        self._last_boost: float = 0.0
        self._last_error: str = ""

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def status(self) -> dict:
        return {
            "configured": self.configured,
            "baseUrl": DEEPSEEK_BASE,
            "model": self.model,
            "lastBoost": self._last_boost,
            "lastError": self._last_error,
            "lastCommentary": self._last_commentary,
        }

    def set_api_key(self, key: str):
        self.api_key = (key or "").strip()
        self._last_error = ""

    async def chat(self, messages: list[dict], temperature: float = 0.4) -> dict:
        if not self.configured:
            return {"ok": False, "error": "DEEPSEEK_API_KEY not set"}
        url = f"{DEEPSEEK_BASE}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 512,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(url, headers=headers, json=body)
                if r.status_code >= 400:
                    self._last_error = f"HTTP {r.status_code}: {r.text[:200]}"
                    return {"ok": False, "error": self._last_error}
                data = r.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                return {"ok": True, "content": content, "raw": data}
        except Exception as e:
            self._last_error = str(e)
            return {"ok": False, "error": self._last_error}

    async def short_trade_commentary(
        self,
        symbol: str,
        price: float,
        consensus: dict,
        top_signals: list[dict],
    ) -> dict:
        """Ask DeepSeek for a short HK/EN trading commentary (not financial advice)."""
        if not self.configured:
            stub = {
                "ok": True,
                "content": (
                    f"[stub] {symbol} @ {price}: consensus {consensus.get('score')} "
                    f"→ {consensus.get('action')}. Set DEEPSEEK_API_KEY for live AI commentary."
                ),
                "stub": True,
            }
            self._last_commentary = stub
            return stub

        sig_lines = ", ".join(
            f"{s.get('name')}={s.get('score')}" for s in top_signals[:8]
        )
        prompt = (
            "You are a crypto short-trading assistant for personal use. "
            "Give 3-5 concise bullet points in Traditional Chinese (HK) + one English line. "
            "No guaranteed returns. Not financial advice.\n"
            f"Symbol: {symbol}\nPrice: {price}\n"
            f"Consensus: {consensus}\nTop signals: {sig_lines}\n"
        )
        result = await self.chat([
            {"role": "system", "content": "Concise crypto short-trade analyst. Personal-use only."},
            {"role": "user", "content": prompt},
        ])
        self._last_commentary = {**result, "ts": time.time(), "symbol": symbol}
        return self._last_commentary

    async def signal_boost(self, symbol: str, consensus_score: float) -> float:
        """Optional AI bias -10..+10 added to consensus. Returns 0 if no key / fail."""
        if not self.configured:
            self._last_boost = 0.0
            return 0.0
        result = await self.chat([
            {"role": "system", "content": "Reply with ONLY a number from -10 to 10 (AI bias for short trade)."},
            {"role": "user", "content": f"{symbol} consensus={consensus_score}. Bias?"},
        ], temperature=0.2)
        if not result.get("ok"):
            self._last_boost = 0.0
            return 0.0
        text = (result.get("content") or "0").strip().split()[0]
        try:
            val = float(text.replace("+", ""))
            val = max(-10.0, min(10.0, val))
        except ValueError:
            val = 0.0
        self._last_boost = val
        return val
