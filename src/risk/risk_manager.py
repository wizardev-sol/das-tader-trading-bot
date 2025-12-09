from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from src.config import RiskSettings
from src.execution.execution_bot import Order

logger = structlog.get_logger(__name__)


@dataclass
class Position:
    symbol: str
    side: str
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss_price: float | None = None
    take_profit_price: float | None = None
    trailing_stop_price: float | None = None


class RiskManager:
    def __init__(self, settings: RiskSettings):
        self.settings = settings
        self.positions: dict[str, Position] = {}
        self.daily_pnl: float = 0.0
        self.daily_loss_limit_reached = False

    def validate_order(self, symbol: str, side: str, quantity: int, price: float) -> tuple[bool, str]:
        position_value = quantity * price

        if position_value > self.settings.max_position_size_usd:
            return (False, f"Position size ${position_value:.2f} exceeds maximum ${self.settings.max_position_size_usd:.2f}")

        if len(self.positions) >= self.settings.max_open_positions:
            return (False, f"Maximum open positions {self.settings.max_open_positions} reached")

        if self.daily_loss_limit_reached:
            return (False, "Daily loss limit reached")

        return (True, "OK")

    def add_position(self, symbol: str, side: str, quantity: int, entry_price: float):
        if symbol in self.positions:
            existing = self.positions[symbol]
            if existing.side == side:
                total_quantity = existing.quantity + quantity
                avg_price = ((existing.quantity * existing.entry_price) + (quantity * entry_price)) / total_quantity
                self.positions[symbol] = Position(
                    symbol=symbol,
                    side=side,
                    quantity=total_quantity,
                    entry_price=avg_price,
                    current_price=entry_price,
                    unrealized_pnl=0.0,
                    stop_loss_price=self._calculate_stop_loss(avg_price, side),
                    take_profit_price=self._calculate_take_profit(avg_price, side),
                    trailing_stop_price=self._calculate_trailing_stop(avg_price, side),
                )
            else:
                if quantity >= existing.quantity:
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        side=side,
                        quantity=quantity - existing.quantity,
                        entry_price=entry_price,
                        current_price=entry_price,
                        unrealized_pnl=0.0,
                        stop_loss_price=self._calculate_stop_loss(entry_price, side),
                        take_profit_price=self._calculate_take_profit(entry_price, side),
                        trailing_stop_price=self._calculate_trailing_stop(entry_price, side),
                    )
                else:
                    self.positions[symbol].quantity -= quantity
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                current_price=entry_price,
                unrealized_pnl=0.0,
                stop_loss_price=self._calculate_stop_loss(entry_price, side),
                take_profit_price=self._calculate_take_profit(entry_price, side),
                trailing_stop_price=self._calculate_trailing_stop(entry_price, side),
            )

        logger.info("position_added", symbol=symbol, side=side, quantity=quantity, entry_price=entry_price)

    def update_position_price(self, symbol: str, current_price: float):
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        position.current_price = current_price

        if position.side == "BUY":
            position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
        else:
            position.unrealized_pnl = (position.entry_price - current_price) * position.quantity

        self._update_trailing_stop(position)

        self.daily_pnl += position.unrealized_pnl - (position.unrealized_pnl - position.unrealized_pnl)

        if self.daily_pnl <= -self.settings.max_daily_loss_usd:
            self.daily_loss_limit_reached = True
            logger.warning("daily_loss_limit_reached", daily_pnl=self.daily_pnl, limit=self.settings.max_daily_loss_usd)

    def check_stop_loss(self, symbol: str) -> bool:
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]

        if position.stop_loss_price:
            if position.side == "BUY" and position.current_price <= position.stop_loss_price:
                return True
            elif position.side == "SELL" and position.current_price >= position.stop_loss_price:
                return True

        return False

    def check_take_profit(self, symbol: str) -> bool:
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]

        if position.take_profit_price:
            if position.side == "BUY" and position.current_price >= position.take_profit_price:
                return True
            elif position.side == "SELL" and position.current_price <= position.take_profit_price:
                return True

        return False

    def remove_position(self, symbol: str):
        if symbol in self.positions:
            position = self.positions[symbol]
            self.daily_pnl += position.unrealized_pnl
            del self.positions[symbol]
            logger.info("position_removed", symbol=symbol, final_pnl=position.unrealized_pnl)

    def _calculate_stop_loss(self, entry_price: float, side: str) -> float:
        if side == "BUY":
            return entry_price * (1 - self.settings.stop_loss_pct / 100)
        else:
            return entry_price * (1 + self.settings.stop_loss_pct / 100)

    def _calculate_take_profit(self, entry_price: float, side: str) -> float:
        if side == "BUY":
            return entry_price * (1 + self.settings.take_profit_pct / 100)
        else:
            return entry_price * (1 - self.settings.take_profit_pct / 100)

    def _calculate_trailing_stop(self, entry_price: float, side: str) -> float:
        if side == "BUY":
            return entry_price * (1 - self.settings.trailing_stop_pct / 100)
        else:
            return entry_price * (1 + self.settings.trailing_stop_pct / 100)

    def _update_trailing_stop(self, position: Position):
        if not position.trailing_stop_price:
            return

        if position.side == "BUY":
            new_trailing = position.current_price * (1 - self.settings.trailing_stop_pct / 100)
            if new_trailing > position.trailing_stop_price:
                position.trailing_stop_price = new_trailing
                position.stop_loss_price = new_trailing
        else:
            new_trailing = position.current_price * (1 + self.settings.trailing_stop_pct / 100)
            if new_trailing < position.trailing_stop_price:
                position.trailing_stop_price = new_trailing
                position.stop_loss_price = new_trailing

    def get_positions(self) -> dict[str, Position]:
        return self.positions.copy()

    def get_daily_pnl(self) -> float:
        return self.daily_pnl

