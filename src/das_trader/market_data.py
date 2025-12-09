from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import quickfix as fix
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MarketData:
    symbol: str
    bid_price: float
    ask_price: float
    last_price: float
    volume: int
    timestamp: float


class MarketDataHandler:
    def __init__(self):
        self.market_data: dict[str, MarketData] = {}
        self.callbacks: list[callable] = []

    def register_callback(self, callback: callable):
        self.callbacks.append(callback)

    def on_market_data_update(self, message: fix.Message):
        try:
            symbol_field = fix.Symbol()
            message.getField(symbol_field)
            symbol = symbol_field.getValue()

            bid_price = self._get_price(message, fix.MDEntryType_BID)
            ask_price = self._get_price(message, fix.MDEntryType_OFFER)
            last_price = self._get_price(message, fix.MDEntryType_TRADE)

            volume_field = fix.MDEntrySize()
            if message.isSetField(volume_field):
                message.getField(volume_field)
                volume = int(volume_field.getValue())
            else:
                volume = 0

            market_data = MarketData(
                symbol=symbol,
                bid_price=bid_price,
                ask_price=ask_price,
                last_price=last_price,
                volume=volume,
                timestamp=time.time(),
            )

            self.market_data[symbol] = market_data

            for callback in self.callbacks:
                callback(market_data)

            logger.debug("market_data_updated", symbol=symbol, bid=bid_price, ask=ask_price, last=last_price)
        except Exception as e:
            logger.error("market_data_parse_error", error=str(e))

    def _get_price(self, message: fix.Message, entry_type: str) -> float:
        try:
            no_md_entries = fix.NoMDEntries()
            message.getField(no_md_entries)
            num_entries = no_md_entries.getValue()

            for i in range(num_entries):
                group = fix.MDEntryType()
                message.getGroup(i + 1, group)
                
                entry_type_field = fix.MDEntryType()
                group.getField(entry_type_field)
                
                if entry_type_field.getValue() == entry_type:
                    price_field = fix.MDEntryPx()
                    group.getField(price_field)
                    return float(price_field.getValue())
        except Exception:
            pass
        
        return 0.0

    def get_market_data(self, symbol: str) -> MarketData | None:
        return self.market_data.get(symbol)

    def get_all_symbols(self) -> list[str]:
        return list(self.market_data.keys())

