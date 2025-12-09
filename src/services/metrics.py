from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, start_http_server

orders_placed_counter = Counter(
    "das_orders_placed_total", "Total orders placed", ["order_type", "side"]
)
orders_filled_counter = Counter(
    "das_orders_filled_total", "Total orders filled", ["order_type", "side"]
)
scanner_signals_counter = Counter(
    "das_scanner_signals_total", "Total scanner signals detected", ["signal_type"]
)
positions_gauge = Gauge("das_open_positions", "Current open positions")
pnl_gauge = Gauge("das_pnl_usd", "Current P&L in USD")
daily_pnl_gauge = Gauge("das_daily_pnl_usd", "Daily P&L in USD")
order_latency_histogram = Histogram(
    "das_order_latency_ms",
    "Order execution latency in milliseconds",
    buckets=[10, 50, 100, 250, 500, 1000],
)


def start_metrics_server(host: str, port: int) -> None:
    start_http_server(port, addr=host)


def record_order_placed(order_type: str, side: str) -> None:
    orders_placed_counter.labels(order_type=order_type, side=side).inc()


def record_order_filled(order_type: str, side: str) -> None:
    orders_filled_counter.labels(order_type=order_type, side=side).inc()


def record_scanner_signal(signal_type: str) -> None:
    scanner_signals_counter.labels(signal_type=signal_type).inc()


def record_positions(count: int) -> None:
    positions_gauge.set(count)


def record_pnl(pnl_usd: float) -> None:
    pnl_gauge.set(pnl_usd)


def record_daily_pnl(pnl_usd: float) -> None:
    daily_pnl_gauge.set(pnl_usd)


def record_order_latency(latency_ms: float) -> None:
    order_latency_histogram.observe(latency_ms)

