from __future__ import annotations

import asyncio
import signal

import structlog
from dotenv import load_dotenv

from src.bots.short_selling_bot import ShortSellingBot
from src.config import Settings, get_settings
from src.das_trader.fix_client import DasTraderFixClient, FixApplication
from src.das_trader.market_data import MarketDataHandler
from src.execution.execution_bot import ExecutionBot
from src.logging_config import configure_logging
from src.risk.risk_manager import RiskManager
from src.scanner.scanner_bot import ScannerBot
from src.services import start_metrics_server

logger = structlog.get_logger(__name__)


class DasTraderBot:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.running = False

        self.fix_application = FixApplication()
        self.fix_client = DasTraderFixClient(settings.das_trader.fix_config_file, self.fix_application)

        self.market_data_handler = MarketDataHandler()
        self.fix_application.on_market_data = self.market_data_handler.on_market_data_update

        self.execution_bot = ExecutionBot(settings.execution, self.fix_client)
        self.risk_manager = RiskManager(settings.risk)
        self.scanner_bot = ScannerBot(settings.scanner, self.market_data_handler)
        self.short_selling_bot = ShortSellingBot(
            settings.short_selling, self.execution_bot, self.market_data_handler
        )

        self._setup_callbacks()

    def _setup_callbacks(self):
        def on_scan_result(scan_result):
            logger.info(
                "scanner_signal",
                symbol=scan_result.symbol,
                signal_type=scan_result.signal_type,
                reason=scan_result.reason,
            )

            if scan_result.signal_type in ["BREAKOUT_UP", "VOLUME_SPIKE"]:
                self._handle_buy_signal(scan_result)
            elif scan_result.signal_type == "BREAKOUT_DOWN":
                self._handle_sell_signal(scan_result)

        self.scanner_bot.register_callback(on_scan_result)

    def _handle_buy_signal(self, scan_result):
        if not self.settings.execution.enabled:
            return

        quantity = 100
        is_valid, reason = self.risk_manager.validate_order(
            scan_result.symbol, "BUY", quantity, scan_result.price
        )

        if not is_valid:
            logger.warning("order_rejected_by_risk", symbol=scan_result.symbol, reason=reason)
            return

        try:
            order_id = self.execution_bot.place_market_order(
                symbol=scan_result.symbol, side="BUY", quantity=quantity
            )
            self.risk_manager.add_position(scan_result.symbol, "BUY", quantity, scan_result.price)
            logger.info("buy_order_executed", symbol=scan_result.symbol, order_id=order_id)
        except Exception as e:
            logger.error("buy_order_failed", symbol=scan_result.symbol, error=str(e))

    def _handle_sell_signal(self, scan_result):
        if not self.settings.execution.enabled:
            return

        positions = self.risk_manager.get_positions()
        if scan_result.symbol not in positions:
            return

        position = positions[scan_result.symbol]
        if position.side == "BUY":
            try:
                order_id = self.execution_bot.place_market_order(
                    symbol=scan_result.symbol, side="SELL", quantity=position.quantity
                )
                self.risk_manager.remove_position(scan_result.symbol)
                logger.info("sell_order_executed", symbol=scan_result.symbol, order_id=order_id)
            except Exception as e:
                logger.error("sell_order_failed", symbol=scan_result.symbol, error=str(e))

    async def run_scanner_loop(self):
        while self.running:
            try:
                if self.settings.scanner.enabled:
                    results = self.scanner_bot.scan()
                    for result in results:
                        logger.debug("scanner_result", result=result)
                await asyncio.sleep(self.settings.scanner.scan_interval_sec)
            except Exception as e:
                logger.error("scanner_loop_error", error=str(e))
                await asyncio.sleep(1)

    async def run_risk_monitoring_loop(self):
        while self.running:
            try:
                if self.settings.risk.enabled:
                    positions = self.risk_manager.get_positions()
                    for symbol, position in positions.items():
                        market_data = self.market_data_handler.get_market_data(symbol)
                        if market_data:
                            self.risk_manager.update_position_price(symbol, market_data.last_price)

                            if self.risk_manager.check_stop_loss(symbol):
                                logger.warning("stop_loss_triggered", symbol=symbol)
                                self.execution_bot.place_market_order(
                                    symbol=symbol,
                                    side="SELL" if position.side == "BUY" else "BUY",
                                    quantity=position.quantity,
                                )
                                self.risk_manager.remove_position(symbol)

                            if self.risk_manager.check_take_profit(symbol):
                                logger.info("take_profit_triggered", symbol=symbol)
                                self.execution_bot.place_market_order(
                                    symbol=symbol,
                                    side="SELL" if position.side == "BUY" else "BUY",
                                    quantity=position.quantity,
                                )
                                self.risk_manager.remove_position(symbol)

                await asyncio.sleep(1.0)
            except Exception as e:
                logger.error("risk_monitoring_error", error=str(e))
                await asyncio.sleep(1)

    async def run_short_selling_loop(self):
        while self.running:
            try:
                if self.settings.short_selling.enabled:
                    opportunities = self.short_selling_bot.scan_short_opportunities()
                    for opp in opportunities:
                        logger.info("short_opportunity_detected", symbol=opp.symbol, drop_pct=opp.drop_pct)
                        self.short_selling_bot.execute_short(opp, quantity=100)
                await asyncio.sleep(5.0)
            except Exception as e:
                logger.error("short_selling_loop_error", error=str(e))
                await asyncio.sleep(1)

    async def run(self):
        self.running = True

        logger.info("das_trader_bot_starting")

        try:
            self.fix_client.start()

            while not self.fix_client.is_logged_on():
                await asyncio.sleep(1)

            logger.info("fix_connection_established")

            tasks = [
                self.run_scanner_loop(),
                self.run_risk_monitoring_loop(),
            ]

            if self.settings.short_selling.enabled:
                tasks.append(self.run_short_selling_loop())

            await asyncio.gather(*tasks)

        finally:
            await self.cleanup()

    async def cleanup(self):
        self.running = False
        self.fix_client.stop()
        logger.info("das_trader_bot_shutdown_complete")


async def bootstrap(settings: Settings):
    load_dotenv()
    configure_logging(settings.log_level)
    start_metrics_server(settings.metrics_host, settings.metrics_port)

    bot = DasTraderBot(settings)

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _handle_signal():
        logger.info("shutdown_signal_received")
        bot.running = False
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            pass

    try:
        await bot.run()
    finally:
        logger.info("bot_shutdown_complete")


def main():
    settings = get_settings()
    asyncio.run(bootstrap(settings))


if __name__ == "__main__":
    main()

