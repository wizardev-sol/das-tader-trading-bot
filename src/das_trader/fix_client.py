from __future__ import annotations

import time

import quickfix as fix
import structlog

logger = structlog.get_logger(__name__)


class FixApplication(fix.Application):
    def __init__(self):
        super().__init__()
        self.session_id: fix.SessionID | None = None
        self.logged_on = False

    def onCreate(self, session_id: fix.SessionID):
        logger.info("fix_session_created", session_id=str(session_id))

    def onLogon(self, session_id: fix.SessionID):
        self.session_id = session_id
        self.logged_on = True
        logger.info("fix_logon_successful", session_id=str(session_id))

    def onLogout(self, session_id: fix.SessionID):
        self.logged_on = False
        logger.info("fix_logout", session_id=str(session_id))

    def toAdmin(self, message: fix.Message, session_id: fix.SessionID):
        pass

    def fromAdmin(self, message: fix.Message, session_id: fix.SessionID):
        pass

    def toApp(self, message: fix.Message, session_id: fix.SessionID):
        pass

    def fromApp(self, message: fix.Message, session_id: fix.SessionID):
        msg_type = fix.MsgType()
        message.getHeader().getField(msg_type)
        
        if msg_type.getValue() == fix.MsgType_MarketDataSnapshotFullRefresh:
            self.on_market_data(message)
        elif msg_type.getValue() == fix.MsgType_ExecutionReport:
            self.on_execution_report(message)

    def on_market_data(self, message: fix.Message):
        pass

    def on_execution_report(self, message: fix.Message):
        pass


class DasTraderFixClient:
    def __init__(self, config_file: str, application: FixApplication):
        self.config_file = config_file
        self.application = application
        self.settings = fix.SessionSettings(config_file)
        self.store_factory = fix.FileStoreFactory(self.settings)
        self.log_factory = fix.FileLogFactory(self.settings)
        self.initiator: fix.SocketInitiator | None = None

    def start(self):
        try:
            self.initiator = fix.SocketInitiator(
                self.application, self.store_factory, self.settings, self.log_factory
            )
            self.initiator.start()
            logger.info("fix_initiator_started")
        except Exception as e:
            logger.error("fix_initiator_start_failed", error=str(e))
            raise

    def stop(self):
        if self.initiator:
            self.initiator.stop()
            logger.info("fix_initiator_stopped")

    def is_logged_on(self) -> bool:
        return self.application.logged_on

    def send_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: int,
        price: float | None = None,
        time_in_force: str = "DAY",
    ) -> str:
        if not self.is_logged_on():
            raise RuntimeError("Not logged on to DAS Trader")

        message = fix.Message()
        header = message.getHeader()

        header.setField(fix.MsgType(fix.MsgType_NewOrderSingle))
        header.setField(fix.SenderCompID(self.application.session_id.getSenderCompID()))
        header.setField(fix.TargetCompID(self.application.session_id.getTargetCompID()))

        message.setField(fix.ClOrdID(f"ORDER_{int(time.time() * 1000)}"))
        message.setField(fix.Symbol(symbol))
        message.setField(fix.Side(fix.Side_BUY if side == "BUY" else fix.Side_SELL))
        message.setField(fix.OrdType(fix.OrdType_LIMIT if order_type == "LIMIT" else fix.OrdType_MARKET))
        message.setField(fix.OrderQty(quantity))
        message.setField(fix.TimeInForce(fix.TimeInForce_DAY if time_in_force == "DAY" else fix.TimeInForce_IOC))

        if price and order_type == "LIMIT":
            message.setField(fix.Price(price))

        try:
            fix.Session.sendToTarget(message, self.application.session_id)
            cl_ord_id = message.getField(fix.ClOrdID()).getValue()
            logger.info("order_sent", symbol=symbol, side=side, quantity=quantity, cl_ord_id=cl_ord_id)
            return cl_ord_id
        except Exception as e:
            logger.error("order_send_failed", error=str(e))
            raise

    def cancel_order(self, order_id: str, symbol: str):
        if not self.is_logged_on():
            raise RuntimeError("Not logged on to DAS Trader")

        message = fix.Message()
        header = message.getHeader()

        header.setField(fix.MsgType(fix.MsgType_OrderCancelRequest))
        header.setField(fix.SenderCompID(self.application.session_id.getSenderCompID()))
        header.setField(fix.TargetCompID(self.application.session_id.getTargetCompID()))

        message.setField(fix.OrigClOrdID(order_id))
        message.setField(fix.ClOrdID(f"CANCEL_{int(time.time() * 1000)}"))
        message.setField(fix.Symbol(symbol))

        try:
            fix.Session.sendToTarget(message, self.application.session_id)
            logger.info("cancel_order_sent", order_id=order_id, symbol=symbol)
        except Exception as e:
            logger.error("cancel_order_failed", error=str(e))
            raise

