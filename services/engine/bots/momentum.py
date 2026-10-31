"""Simple momentum bot — trades on consensus score thresholds."""
from __future__ import annotations
import time
from dataclasses import dataclass, asdict
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from exchange.paper import PaperExchange

@dataclass
class BotConfig:
    id: str = "momentum-1"
    name: str = "Simple Momentum"
    enabled: bool = False
    symbol: str = "BTCUSDT"
    buy_threshold: float = 25.0
    sell_threshold: float = -25.0
    order_notional_usd: float = 25.0
    cooldown_sec: float = 30.0
    last_action_ts: float = 0.0
    last_action: str = "idle"
    last_error: str = ""

class MomentumBot:
    def __init__(self, exchange: "PaperExchange", cfg: Optional[BotConfig] = None):
        self.exchange = exchange
        self.cfg = cfg or BotConfig()

    def status(self) -> dict:
        return asdict(self.cfg)

    def set_enabled(self, enabled: bool):
        self.cfg.enabled = enabled
        if not enabled:
            self.cfg.last_action = "stopped"

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self.cfg, k) and k not in ("id",):
                setattr(self.cfg, k, v)

    def tick(self, consensus_score: float) -> Optional[dict]:
        if not self.cfg.enabled:
            return None
        if self.exchange.state.kill_switch:
            self.cfg.last_error = "kill-switch active"
            return None
        now = time.time()
        if now - self.cfg.last_action_ts < self.cfg.cooldown_sec:
            return None

        px = self.exchange.price(self.cfg.symbol)
        if px <= 0:
            return None
        qty = round(self.cfg.order_notional_usd / px, 8)
        result = None
        if consensus_score >= self.cfg.buy_threshold:
            result = self.exchange.place_order(self.cfg.symbol, "buy", qty, order_type="market")
            self.cfg.last_action = "buy" if result.get("ok") else "buy_fail"
        elif consensus_score <= self.cfg.sell_threshold:
            held = self.exchange.state.positions.get(self.cfg.symbol, 0.0)
            if held <= 0:
                self.cfg.last_action = "no_position"
                return None
            sell_qty = min(qty, held)
            result = self.exchange.place_order(self.cfg.symbol, "sell", sell_qty, order_type="market")
            self.cfg.last_action = "sell" if result.get("ok") else "sell_fail"
        else:
            self.cfg.last_action = "hold"
            return None

        self.cfg.last_action_ts = now
        self.cfg.last_error = "" if result and result.get("ok") else (result or {}).get("error", "")
        return result
