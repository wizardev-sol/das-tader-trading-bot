from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from src.config import ShortSellingSettings
from src.das_trader.market_data import MarketData, MarketDataHandler
from src.execution.execution_bot import ExecutionBot

logger = structlog.get_logger(__name__)


@dataclass
class ShortOpportunity:
    symbol: str
    entry_price: float
    drop_pct: float
    reason: str


class ShortSellingBot:
    def __init__(
        self,
        settings: ShortSellingSettings,
        execution_bot: ExecutionBot,
        market_data_handler: MarketDataHandler,
    ):
        self.settings = settings
        self.execution_bot = execution_bot
        self.market_data_handler = market_data_handler
        self.short_positions: dict[str, int] = {}
        self.previous_prices: dict[str, float] = {}

    def scan_short_opportunities(self) -> list[ShortOpportunity]:
        opportunities = []
        current_data = self.market_data_handler.market_data

        for symbol, data in current_data.items():
            if symbol in self.short_positions:
                continue

            previous_price = self.previous_prices.get(symbol)
            if not previous_price:
                self.previous_prices[symbol] = data.last_price
                continue

            drop_pct = ((data.last_price - previous_price) / previous_price) * 100

            if drop_pct <= self.settings.short_entry_threshold_pct:
                opportunity = ShortOpportunity(
                    symbol=symbol,
                    entry_price=data.last_price,
                    drop_pct=drop_pct,
                    reason=f"Price drop: {drop_pct:.2f}%",
                )
                opportunities.append(opportunity)

            self.previous_prices[symbol] = data.last_price

        return opportunities

    def execute_short(self, opportunity: ShortOpportunity, quantity: int) -> str | None:
        if not self.settings.enabled:
            logger.warning("short_selling_disabled")
            return None

        current_position = self.short_positions.get(opportunity.symbol, 0)
        if current_position + quantity > self.settings.max_short_position:
            logger.warning(
                "short_position_limit_exceeded",
                symbol=opportunity.symbol,
                current=current_position,
                requested=quantity,
                max=self.settings.max_short_position,
            )
            return None

        if self.settings.locate_required:
            if not self._check_locate(opportunity.symbol, quantity):
                logger.warning("locate_not_available", symbol=opportunity.symbol, quantity=quantity)
                return None

        try:
            order_id = self.execution_bot.place_market_order(
                symbol=opportunity.symbol, side="SELL", quantity=quantity
            )
            self.short_positions[opportunity.symbol] = current_position + quantity
            logger.info(
                "short_position_opened",
                symbol=opportunity.symbol,
                quantity=quantity,
                entry_price=opportunity.entry_price,
                order_id=order_id,
            )
            return order_id
        except Exception as e:
            logger.error("short_execution_failed", symbol=opportunity.symbol, error=str(e))
            return None

    def close_short_position(self, symbol: str, quantity: int | None = None) -> str | None:
        current_position = self.short_positions.get(symbol, 0)
        if current_position == 0:
            logger.warning("no_short_position", symbol=symbol)
            return None

        close_quantity = quantity or current_position

        try:
            order_id = self.execution_bot.place_market_order(symbol=symbol, side="BUY", quantity=close_quantity)
            self.short_positions[symbol] = max(0, current_position - close_quantity)
            logger.info("short_position_closed", symbol=symbol, quantity=close_quantity, order_id=order_id)
            return order_id
        except Exception as e:
            logger.error("short_close_failed", symbol=symbol, error=str(e))
            return None

    def _check_locate(self, symbol: str, quantity: int) -> bool:
        # In production, this would check with the broker for locate availability
        # For now, return True as a placeholder
        return True

    def get_short_positions(self) -> dict[str, int]:
        return self.short_positions.copy()

