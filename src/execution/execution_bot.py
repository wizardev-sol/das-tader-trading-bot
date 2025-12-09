from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from src.config import ExecutionSettings
from src.das_trader.fix_client import DasTraderFixClient

logger = structlog.get_logger(__name__)


@dataclass
class Order:
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: int
    price: float | None
    time_in_force: str
    status: str = "PENDING"
    filled_quantity: int = 0
    avg_fill_price: float = 0.0


class ExecutionBot:
    def __init__(self, settings: ExecutionSettings, fix_client: DasTraderFixClient):
        self.settings = settings
        self.fix_client = fix_client
        self.orders: dict[str, Order] = {}

    def place_market_order(self, symbol: str, side: str, quantity: int) -> str:
        if quantity > self.settings.max_order_size:
            raise ValueError(f"Order size {quantity} exceeds maximum {self.settings.max_order_size}")

        try:
            order_id = self.fix_client.send_order(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity,
                time_in_force=self.settings.default_time_in_force,
            )

            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity,
                price=None,
                time_in_force=self.settings.default_time_in_force,
                status="SUBMITTED",
            )

            self.orders[order_id] = order
            logger.info("market_order_placed", symbol=symbol, side=side, quantity=quantity, order_id=order_id)
            return order_id
        except Exception as e:
            logger.error("market_order_failed", symbol=symbol, side=side, error=str(e))
            raise

    def place_limit_order(
        self, symbol: str, side: str, quantity: int, price: float, time_in_force: str | None = None
    ) -> str:
        if quantity > self.settings.max_order_size:
            raise ValueError(f"Order size {quantity} exceeds maximum {self.settings.max_order_size}")

        try:
            tif = time_in_force or self.settings.default_time_in_force
            order_id = self.fix_client.send_order(
                symbol=symbol,
                side=side,
                order_type="LIMIT",
                quantity=quantity,
                price=price,
                time_in_force=tif,
            )

            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type="LIMIT",
                quantity=quantity,
                price=price,
                time_in_force=tif,
                status="SUBMITTED",
            )

            self.orders[order_id] = order
            logger.info(
                "limit_order_placed", symbol=symbol, side=side, quantity=quantity, price=price, order_id=order_id
            )
            return order_id
        except Exception as e:
            logger.error("limit_order_failed", symbol=symbol, side=side, error=str(e))
            raise

    def place_stop_order(self, symbol: str, side: str, quantity: int, stop_price: float) -> str:
        if quantity > self.settings.max_order_size:
            raise ValueError(f"Order size {quantity} exceeds maximum {self.settings.max_order_size}")

        try:
            order_id = self.fix_client.send_order(
                symbol=symbol,
                side=side,
                order_type="STOP",
                quantity=quantity,
                price=stop_price,
                time_in_force=self.settings.default_time_in_force,
            )

            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type="STOP",
                quantity=quantity,
                price=stop_price,
                time_in_force=self.settings.default_time_in_force,
                status="SUBMITTED",
            )

            self.orders[order_id] = order
            logger.info(
                "stop_order_placed", symbol=symbol, side=side, quantity=quantity, stop_price=stop_price, order_id=order_id
            )
            return order_id
        except Exception as e:
            logger.error("stop_order_failed", symbol=symbol, side=side, error=str(e))
            raise

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        try:
            self.fix_client.cancel_order(order_id, symbol)
            if order_id in self.orders:
                self.orders[order_id].status = "CANCELLED"
            logger.info("order_cancelled", order_id=order_id, symbol=symbol)
            return True
        except Exception as e:
            logger.error("order_cancel_failed", order_id=order_id, error=str(e))
            return False

    def get_order(self, order_id: str) -> Order | None:
        return self.orders.get(order_id)

    def get_open_orders(self) -> list[Order]:
        return [order for order in self.orders.values() if order.status in ["SUBMITTED", "PARTIALLY_FILLED"]]

