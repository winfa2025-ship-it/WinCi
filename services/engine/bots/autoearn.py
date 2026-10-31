"""AutoEarn — opt-in momentum bot with extra risk knobs. Never guarantees profit."""
from __future__ import annotations
import time
from dataclasses import dataclass, asdict
from typing import Optional, TYPE_CHECKING

from bots.momentum import MomentumBot, BotConfig

if TYPE_CHECKING:
    from exchange.paper import PaperExchange

DISCLAIMER_ZH = "唔保證盈利／過去表現唔代表將來"
DISCLAIMER_EN = "No guaranteed profit. Past performance does not indicate future results."


@dataclass
class AutoEarnConfig(BotConfig):
    id: str = "autoearn-1"
    name: str = "AutoEarn"
    enabled: bool = False
    symbol: str = "BTCUSDT"
    buy_threshold: float = 20.0
    sell_threshold: float = -20.0
    order_notional_usd: float = 25.0  # position size USD per order
    cooldown_sec: float = 20.0
    max_daily_loss_pct: float = 5.0  # % of starting equity
    kill_switch: bool = False  # local kill (also respects exchange kill)
    starting_equity_ref: float = 0.0
    last_action_ts: float = 0.0
    last_action: str = "idle"
    last_error: str = ""


class AutoEarnBot(MomentumBot):
    """Extends momentum with daily loss % and explicit kill switch."""

    def __init__(self, exchange: "PaperExchange", cfg: Optional[AutoEarnConfig] = None):
        self.exchange = exchange
        self.cfg: AutoEarnConfig = cfg or AutoEarnConfig()

    def status(self) -> dict:
        d = asdict(self.cfg)
        d["disclaimerZh"] = DISCLAIMER_ZH
        d["disclaimerEn"] = DISCLAIMER_EN
        d["kind"] = "autoearn"
        return d

    def set_enabled(self, enabled: bool):
        if enabled and self.cfg.starting_equity_ref <= 0:
            pf = self.exchange.portfolio()
            self.cfg.starting_equity_ref = float(pf.get("equity") or 10000.0)
        self.cfg.enabled = enabled
        if not enabled:
            self.cfg.last_action = "stopped"

    def set_kill(self, active: bool, reason: str = "user kill switch"):
        self.cfg.kill_switch = active
        if active:
            self.cfg.enabled = False
            self.cfg.last_action = "killed"
            self.cfg.last_error = reason
        else:
            self.cfg.last_error = ""

    def update(self, **kwargs):
        # map frontend aliases
        if "position_size_usd" in kwargs:
            kwargs["order_notional_usd"] = kwargs.pop("position_size_usd")
        for k, v in kwargs.items():
            if hasattr(self.cfg, k) and k not in ("id", "kind"):
                setattr(self.cfg, k, v)

    def tick(self, consensus_score: float) -> Optional[dict]:
        if not self.cfg.enabled:
            return None
        if self.cfg.kill_switch:
            self.cfg.last_error = "autoearn kill-switch"
            return None
        if self.exchange.state.kill_switch:
            self.cfg.last_error = "exchange kill-switch active"
            return None

        # daily loss % vs reference equity
        pf = self.exchange.portfolio()
        ref = self.cfg.starting_equity_ref or float(pf.get("equity") or 1.0)
        pnl = float(pf.get("realizedPnlToday") or 0.0)
        loss_pct = (-pnl / ref) * 100.0 if pnl < 0 and ref > 0 else 0.0
        if loss_pct >= self.cfg.max_daily_loss_pct:
            self.set_kill(True, f"max daily loss {self.cfg.max_daily_loss_pct}% hit ({loss_pct:.2f}%)")
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
