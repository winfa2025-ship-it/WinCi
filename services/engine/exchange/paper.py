"""Paper exchange simulator — demo trades without Binance keys."""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import math
import hashlib

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT",
]

BASE_PRICES = {
    "BTCUSDT": 68000.0, "ETHUSDT": 3500.0, "BNBUSDT": 600.0,
    "SOLUSDT": 180.0, "XRPUSDT": 0.55, "DOGEUSDT": 0.15,
    "ADAUSDT": 0.45, "AVAXUSDT": 35.0, "LINKUSDT": 15.0, "MATICUSDT": 0.7,
}

@dataclass
class Order:
    id: str
    symbol: str
    side: str  # buy | sell
    type: str  # market | limit
    quantity: float
    price: float
    notional: float
    status: str
    ts: float
    mode: str = "paper"

@dataclass
class Fill:
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    notional: float
    fee: float
    ts: float

@dataclass
class PaperState:
    usdt: float
    positions: Dict[str, float] = field(default_factory=dict)  # base qty
    avg_cost: Dict[str, float] = field(default_factory=dict)
    orders: List[Order] = field(default_factory=list)
    fills: List[Fill] = field(default_factory=list)
    realized_pnl_today: float = 0.0
    day_key: str = ""
    kill_switch: bool = False
    kill_reason: str = ""

class PaperExchange:
    def __init__(self, starting_usdt: float, min_notional: float, max_position: float, daily_loss: float):
        self.min_notional = min_notional
        self.max_position = max_position
        self.daily_loss = daily_loss
        self.state = PaperState(usdt=starting_usdt)
        self._prices: Dict[str, float] = dict(BASE_PRICES)

    def tick_prices(self, now: Optional[float] = None) -> Dict[str, dict]:
        now = now or time.time()
        out = {}
        for sym, base in BASE_PRICES.items():
            h = hashlib.sha256(f"{sym}:{int(now // 2)}".encode()).hexdigest()
            noise = (int(h[:6], 16) / 0xFFFFFF - 0.5) * 0.004
            wave = math.sin(now / 30 + int(h[6:8], 16)) * 0.002
            px = base * (1 + noise + wave)
            self._prices[sym] = round(px, 8 if px < 1 else 2)
            chg = (noise + wave) * 100
            out[sym] = {
                "symbol": sym,
                "price": self._prices[sym],
                "change24h": round(chg * 12, 2),
                "ts": now,
            }
        return out

    def price(self, symbol: str) -> float:
        return self._prices.get(symbol, BASE_PRICES.get(symbol, 1.0))

    def _roll_day(self, now: float):
        key = time.strftime("%Y-%m-%d", time.localtime(now))
        if self.state.day_key != key:
            self.state.day_key = key
            self.state.realized_pnl_today = 0.0
            # do not auto-clear kill; user resets in settings

    def portfolio(self) -> dict:
        now = time.time()
        self.tick_prices(now)
        positions = []
        equity = self.state.usdt
        for sym, qty in self.state.positions.items():
            if abs(qty) < 1e-12:
                continue
            px = self.price(sym)
            cost = self.state.avg_cost.get(sym, px)
            upnl = (px - cost) * qty
            notional = px * qty
            equity += notional
            positions.append({
                "symbol": sym, "quantity": qty, "avgCost": cost,
                "price": px, "notional": round(notional, 4),
                "unrealizedPnl": round(upnl, 4),
            })
        return {
            "usdt": round(self.state.usdt, 4),
            "equity": round(equity, 4),
            "positions": positions,
            "realizedPnlToday": round(self.state.realized_pnl_today, 4),
            "killSwitch": self.state.kill_switch,
            "killReason": self.state.kill_reason,
            "mode": "paper",
        }

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> dict:
        now = time.time()
        self._roll_day(now)
        if self.state.kill_switch:
            return {"ok": False, "error": f"kill-switch: {self.state.kill_reason}"}
        if symbol not in BASE_PRICES:
            return {"ok": False, "error": f"unknown symbol {symbol}"}
        side = side.lower()
        if side not in ("buy", "sell"):
            return {"ok": False, "error": "side must be buy|sell"}
        if quantity <= 0:
            return {"ok": False, "error": "quantity must be > 0"}

        self.tick_prices(now)
        px = float(price) if (order_type == "limit" and price) else self.price(symbol)
        notional = px * quantity
        if notional < self.min_notional:
            return {"ok": False, "error": f"min notional ${self.min_notional} USD (got {notional:.4f})"}

        if side == "buy":
            pos_notional = abs(self.state.positions.get(symbol, 0.0) * px) + notional
            if pos_notional > self.max_position:
                return {"ok": False, "error": f"max position ${self.max_position} USD"}
            if self.state.usdt < notional:
                return {"ok": False, "error": "insufficient USDT"}
            self.state.usdt -= notional
            prev = self.state.positions.get(symbol, 0.0)
            prev_cost = self.state.avg_cost.get(symbol, px)
            new_qty = prev + quantity
            if new_qty > 0:
                self.state.avg_cost[symbol] = (prev * prev_cost + quantity * px) / new_qty
            self.state.positions[symbol] = new_qty
        else:
            held = self.state.positions.get(symbol, 0.0)
            if quantity > held + 1e-12:
                return {"ok": False, "error": "insufficient position"}
            cost = self.state.avg_cost.get(symbol, px)
            pnl = (px - cost) * quantity
            self.state.usdt += notional
            self.state.realized_pnl_today += pnl
            self.state.positions[symbol] = held - quantity
            if self.state.positions[symbol] <= 1e-12:
                self.state.positions[symbol] = 0.0
                self.state.avg_cost.pop(symbol, None)

        fee = notional * 0.001
        self.state.usdt -= fee
        oid = str(uuid.uuid4())[:8]
        order = Order(
            id=oid, symbol=symbol, side=side, type=order_type,
            quantity=quantity, price=px, notional=round(notional, 6),
            status="filled", ts=now, mode="paper",
        )
        fill = Fill(
            order_id=oid, symbol=symbol, side=side, quantity=quantity,
            price=px, notional=round(notional, 6), fee=round(fee, 6), ts=now,
        )
        self.state.orders.insert(0, order)
        self.state.fills.insert(0, fill)
        self.state.orders = self.state.orders[:200]
        self.state.fills = self.state.fills[:200]

        if self.state.realized_pnl_today <= -abs(self.daily_loss):
            self.state.kill_switch = True
            self.state.kill_reason = f"daily loss limit ${self.daily_loss}"

        return {"ok": True, "order": asdict(order), "fill": asdict(fill)}

    def reset_kill(self):
        self.state.kill_switch = False
        self.state.kill_reason = ""

    def recent_orders(self, n: int = 50) -> list:
        return [asdict(o) for o in self.state.orders[:n]]

    def recent_fills(self, n: int = 50) -> list:
        return [asdict(f) for f in self.state.fills[:n]]
