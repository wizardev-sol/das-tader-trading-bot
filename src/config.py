from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DasTraderSettings(BaseModel):
    sender_comp_id: str = Field(description="FIX SenderCompID")
    target_comp_id: str = Field(default="DAS", description="FIX TargetCompID")
    socket_connect_host: str = Field(default="localhost", description="DAS Trader host")
    socket_connect_port: int = Field(default=9876, description="DAS Trader FIX port")
    username: str = Field(description="DAS Trader username")
    password: str = Field(description="DAS Trader password")
    fix_config_file: str = Field(default="config/das_trader.cfg", description="FIX config file path")


class ScannerSettings(BaseModel):
    enabled: bool = Field(default=True, description="Enable scanner bot")
    scan_interval_sec: float = Field(default=1.0, description="Scanner refresh interval")
    price_breakout_threshold_pct: float = Field(default=2.0, description="Price breakout threshold %")
    volume_spike_threshold: float = Field(default=2.0, description="Volume spike multiplier")
    min_price: float = Field(default=1.0, description="Minimum stock price")
    max_price: float = Field(default=1000.0, description="Maximum stock price")
    min_volume: int = Field(default=100000, description="Minimum daily volume")


class ExecutionSettings(BaseModel):
    enabled: bool = Field(default=True, description="Enable execution bot")
    default_order_type: str = Field(default="LIMIT", description="Default order type: MARKET, LIMIT, STOP")
    default_time_in_force: str = Field(default="DAY", description="Time in force: DAY, IOC, FOK")
    max_order_size: int = Field(default=1000, description="Maximum shares per order")
    slippage_limit_pct: float = Field(default=0.5, description="Maximum slippage %")


class ShortSellingSettings(BaseModel):
    enabled: bool = Field(default=False, description="Enable short selling bot")
    locate_required: bool = Field(default=True, description="Require locate before shorting")
    max_short_position: int = Field(default=500, description="Maximum short position size")
    short_entry_threshold_pct: float = Field(default=-1.0, description="Short entry price drop %")


class RiskSettings(BaseModel):
    enabled: bool = Field(default=True, description="Enable risk management bot")
    max_position_size_usd: float = Field(default=50000.0, description="Maximum position value USD")
    max_daily_loss_usd: float = Field(default=5000.0, description="Maximum daily loss USD")
    stop_loss_pct: float = Field(default=2.0, description="Stop loss percentage")
    trailing_stop_pct: float = Field(default=1.0, description="Trailing stop percentage")
    take_profit_pct: float = Field(default=5.0, description="Take profit percentage")
    max_open_positions: int = Field(default=10, description="Maximum open positions")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    # DAS Trader FIX connection
    das_trader: DasTraderSettings = Field(default_factory=DasTraderSettings)

    # Bot configurations
    scanner: ScannerSettings = Field(default_factory=ScannerSettings)
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)
    short_selling: ShortSellingSettings = Field(default_factory=ShortSellingSettings)
    risk: RiskSettings = Field(default_factory=RiskSettings)

    # Trading symbols
    symbols: list[str] = Field(default=["AAPL", "MSFT", "GOOGL"], description="Symbols to trade")

    # Metrics and logging
    metrics_host: str = "0.0.0.0"
    metrics_port: int = 9306


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

