from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import structlog

from src.config import ScannerSettings
from src.das_trader.market_data import MarketData, MarketDataHandler

logger = structlog.get_logger(__name__)


@dataclass
class ScanResult:
    symbol: str
    signal_type: str
    reason: str
    price: float
    volume: int
    change_pct: float


class ScannerBot:
    def __init__(self, settings: ScannerSettings, market_data_handler: MarketDataHandler):
        self.settings = settings
        self.market_data_handler = market_data_handler
        self.previous_data: dict[str, MarketData] = {}
        self.callbacks: list[Callable[[ScanResult], None]] = []

    def register_callback(self, callback: Callable[[ScanResult], None]):
        self.callbacks.append(callback)

    def scan(self) -> list[ScanResult]:
        results = []
        current_data = self.market_data_handler.market_data

        for symbol, current in current_data.items():
            if not self._is_valid_symbol(current):
                continue

            previous = self.previous_data.get(symbol)

            if previous:
                result = self._analyze_symbol(symbol, previous, current)
                if result:
                    results.append(result)
                    for callback in self.callbacks:
                        callback(result)

            self.previous_data[symbol] = current

        return results

    def _is_valid_symbol(self, data: MarketData) -> bool:
        if data.last_price < self.settings.min_price or data.last_price > self.settings.max_price:
            return False
        if data.volume < self.settings.min_volume:
            return False
        return True

    def _analyze_symbol(self, symbol: str, previous: MarketData, current: MarketData) -> ScanResult | None:
        change_pct = ((current.last_price - previous.last_price) / previous.last_price) * 100

        volume_ratio = current.volume / previous.volume if previous.volume > 0 else 1.0

        if abs(change_pct) >= self.settings.price_breakout_threshold_pct:
            signal_type = "BREAKOUT_UP" if change_pct > 0 else "BREAKOUT_DOWN"
            return ScanResult(
                symbol=symbol,
                signal_type=signal_type,
                reason=f"Price breakout: {change_pct:.2f}%",
                price=current.last_price,
                volume=current.volume,
                change_pct=change_pct,
            )

        if volume_ratio >= self.settings.volume_spike_threshold:
            signal_type = "VOLUME_SPIKE"
            return ScanResult(
                symbol=symbol,
                signal_type=signal_type,
                reason=f"Volume spike: {volume_ratio:.2f}x",
                price=current.last_price,
                volume=current.volume,
                change_pct=change_pct,
            )

        return None

