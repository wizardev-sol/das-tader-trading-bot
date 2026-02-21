# DAS Trader Trading Bot

Production-grade **DAS Trader automated trading bot** with FIX protocol integration, real-time market scanning, order execution, short selling, and comprehensive risk management.  
Built for professional traders seeking automated execution, opportunity detection, and intelligent position management on DAS Trader platform.

Builder: [@vvizardev](https://t.me/vvizardev)

## What This Bot Does

The DAS Trader Bot provides:

- **Real-time market scanning** – Continuously monitors live market data for trading opportunities
- **Automated order execution** – Market, limit, and stop orders with fast execution
- **Short selling automation** – Detects and executes short selling opportunities
- **Risk management** – Stop-loss, take-profit, trailing stops, and position limits
- **FIX protocol integration** – Direct connection to DAS Trader via FIX API
- **Multi-bot architecture** – Modular design supporting multiple trading strategies simultaneously

## Core Features

### 1. Scanner Bot

Continuously monitors live market data and identifies trading opportunities:

- **Price breakout detection** – Identifies stocks breaking above/below key levels
- **Volume spike detection** – Detects unusual volume activity
- **Real-time market data** – Processes live price, volume, and order book updates
- **Configurable thresholds** – Customizable breakout and volume spike parameters
- **Multi-symbol scanning** – Monitors multiple symbols simultaneously

**Use Cases:**
- Automatically detect breakouts and volume spikes
- Alert on price movements exceeding thresholds
- Identify momentum opportunities in real-time

### 2. Order Execution Bot

Automated order placement and management:

- **Market orders** – Fast execution at current market price
- **Limit orders** – Price-controlled execution
- **Stop orders** – Stop-loss and stop-entry orders
- **Order cancellation** – Cancel pending orders
- **Order tracking** – Monitor order status and fills

**Use Cases:**
- Execute trades automatically based on scanner signals
- Place limit orders at specific price levels
- Implement stop-loss orders for risk protection

### 3. Short Selling Bot

Specialized bot for short selling opportunities:

- **Short opportunity detection** – Identifies price drops suitable for shorting
- **Locate checking** – Verifies share availability before shorting
- **Position management** – Tracks and manages short positions
- **Auto-close logic** – Closes short positions based on criteria

**Use Cases:**
- Automatically short stocks on price drops
- Manage short position risk
- Close shorts at profit targets

### 4. Risk Management Bot

Comprehensive risk controls and position monitoring:

- **Stop-loss orders** – Automatic stop-loss placement and adjustment
- **Take-profit targets** – Automatic profit-taking at target levels
- **Trailing stops** – Dynamic stop-loss that follows price movement
- **Position size limits** – Maximum position size per symbol
- **Daily loss limits** – Automatic trading halt on daily loss threshold
- **Open position limits** – Maximum number of concurrent positions

**Use Cases:**
- Protect capital with automatic stop-losses
- Lock in profits with take-profit orders
- Limit exposure with position size controls
- Prevent excessive losses with daily limits

### 5. Real-Time Market Data

Live market data feed processing:

- **FIX protocol integration** – Direct connection to DAS Trader market data
- **Price updates** – Real-time bid/ask/last price updates
- **Volume tracking** – Live volume data for analysis
- **Order book data** – Access to order book depth
- **Low latency** – Fast data processing for quick decisions

## Technical Architecture

```
┌─────────────────────┐      ┌──────────────────────┐      ┌──────────────────┐
│ DAS Trader          │      │ FIX Protocol Client  │      │ Market Data      │
│ (FIX API)           │ <--> │ (QuickFIX)           │ <--> │ Handler          │
└─────────────────────┘      └──────────────────────┘      └──────────────────┘
         │                           │                            │
         │                           v                            │
         │                  ┌──────────────────┐                 │
         │                  │ Scanner Bot       │                 │
         │                  │ (Opportunities)   │                 │
         │                  └──────────────────┘                 │
         │                           │                            │
         v                           v                            v
┌─────────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ Execution Bot       │      │ Short Selling Bot │      │ Risk Manager     │
│ (Order Placement)   │      │ (Short Detection) │      │ (Stop/Take)      │
└─────────────────────┘      └──────────────────┘      └──────────────────┘
```

### Key Modules

- `src/das_trader/fix_client.py` – FIX protocol client for DAS Trader connection
- `src/das_trader/market_data.py` – Real-time market data handler
- `src/scanner/scanner_bot.py` – Market scanner for opportunity detection
- `src/execution/execution_bot.py` – Order execution engine
- `src/bots/short_selling_bot.py` – Short selling automation
- `src/risk/risk_manager.py` – Risk management and position monitoring
- `src/main.py` – Main orchestrator coordinating all bots

## Getting Started

### 1. Requirements

- Python **3.11+**
- **DAS Trader** installed and configured
- **FIX API access** enabled in DAS Trader
- **DAS Trader credentials** (username, password, SenderCompID)
- **Network access** to DAS Trader FIX server (typically localhost:9876)

### 2. Installation

```bash
git clone https://github.com/wizardev-sol/das-trader-bot.git
cd das-trader-bot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Note:** `quickfix` requires compilation. On Windows, you may need Visual C++ Build Tools.  
On Linux/Mac, ensure `g++` and `python-dev` packages are installed.

### 3. Configure FIX Connection

Edit `config/das_trader.cfg`:

```ini
[DEFAULT]
SenderCompID=YOUR_SENDER_COMP_ID
TargetCompID=DAS
SocketConnectHost=localhost
SocketConnectPort=9876
Username=YOUR_USERNAME
Password=YOUR_PASSWORD
```

### 4. Configure Environment

Create a `.env` file:

```env
ENVIRONMENT=production
LOG_LEVEL=INFO

# DAS Trader FIX Settings
DAS_TRADER__SENDER_COMP_ID=YOUR_SENDER_COMP_ID
DAS_TRADER__TARGET_COMP_ID=DAS
DAS_TRADER__SOCKET_CONNECT_HOST=localhost
DAS_TRADER__SOCKET_CONNECT_PORT=9876
DAS_TRADER__USERNAME=YOUR_USERNAME
DAS_TRADER__PASSWORD=YOUR_PASSWORD
DAS_TRADER__FIX_CONFIG_FILE=config/das_trader.cfg

# Scanner Bot
SCANNER__ENABLED=true
SCANNER__SCAN_INTERVAL_SEC=1.0
SCANNER__PRICE_BREAKOUT_THRESHOLD_PCT=2.0
SCANNER__VOLUME_SPIKE_THRESHOLD=2.0
SCANNER__MIN_PRICE=1.0
SCANNER__MAX_PRICE=1000.0
SCANNER__MIN_VOLUME=100000

# Execution Bot
EXECUTION__ENABLED=true
EXECUTION__DEFAULT_ORDER_TYPE=LIMIT
EXECUTION__DEFAULT_TIME_IN_FORCE=DAY
EXECUTION__MAX_ORDER_SIZE=1000
EXECUTION__SLIPPAGE_LIMIT_PCT=0.5

# Short Selling Bot
SHORT_SELLING__ENABLED=false
SHORT_SELLING__LOCATE_REQUIRED=true
SHORT_SELLING__MAX_SHORT_POSITION=500
SHORT_SELLING__SHORT_ENTRY_THRESHOLD_PCT=-1.0

# Risk Management
RISK__ENABLED=true
RISK__MAX_POSITION_SIZE_USD=50000.0
RISK__MAX_DAILY_LOSS_USD=5000.0
RISK__STOP_LOSS_PCT=2.0
RISK__TRAILING_STOP_PCT=1.0
RISK__TAKE_PROFIT_PCT=5.0
RISK__MAX_OPEN_POSITIONS=10

# Trading Symbols
SYMBOLS=["AAPL","MSFT","GOOGL"]

# Metrics
METRICS_HOST=0.0.0.0
METRICS_PORT=9306
```

### 5. Run the Bot

```bash
python -m src.main
```

The bot will:
- Connect to DAS Trader via FIX protocol
- Start receiving real-time market data
- Begin scanning for trading opportunities
- Execute trades based on scanner signals
- Monitor positions and manage risk
- Log all operations and expose Prometheus metrics

### 6. Docker Deployment

```bash
docker compose up --build -d
```

View logs:
```bash
docker compose logs -f das-trader-bot
```

## Bot Configuration Guide

### Scanner Bot Parameters

- **SCAN_INTERVAL_SEC**: How often to scan for opportunities (default: 1.0s)
- **PRICE_BREAKOUT_THRESHOLD_PCT**: Minimum price change to trigger breakout (default: 2.0%)
- **VOLUME_SPIKE_THRESHOLD**: Volume multiplier for spike detection (default: 2.0x)
- **MIN_PRICE / MAX_PRICE**: Price range filter for symbols
- **MIN_VOLUME**: Minimum daily volume filter

### Execution Bot Parameters

- **DEFAULT_ORDER_TYPE**: MARKET, LIMIT, or STOP
- **DEFAULT_TIME_IN_FORCE**: DAY, IOC (Immediate or Cancel), FOK (Fill or Kill)
- **MAX_ORDER_SIZE**: Maximum shares per order
- **SLIPPAGE_LIMIT_PCT**: Maximum acceptable slippage

### Short Selling Bot Parameters

- **ENABLED**: Enable/disable short selling bot
- **LOCATE_REQUIRED**: Require locate before shorting (recommended: true)
- **MAX_SHORT_POSITION**: Maximum short position size
- **SHORT_ENTRY_THRESHOLD_PCT**: Price drop % to trigger short entry

### Risk Management Parameters

- **MAX_POSITION_SIZE_USD**: Maximum position value in USD
- **MAX_DAILY_LOSS_USD**: Daily loss limit (trading halts if exceeded)
- **STOP_LOSS_PCT**: Stop-loss percentage (default: 2.0%)
- **TRAILING_STOP_PCT**: Trailing stop percentage (default: 1.0%)
- **TAKE_PROFIT_PCT**: Take-profit percentage (default: 5.0%)
- **MAX_OPEN_POSITIONS**: Maximum concurrent positions

## Monitoring & Observability

### Prometheus Metrics

Access metrics at: `http://localhost:9306/metrics`

Key metrics:
- `das_orders_placed_total` – Total orders placed by type and side
- `das_orders_filled_total` – Total orders filled
- `das_scanner_signals_total` – Scanner signals detected by type
- `das_open_positions` – Current open positions count
- `das_pnl_usd` – Current P&L in USD
- `das_daily_pnl_usd` – Daily P&L in USD
- `das_order_latency_ms` – Order execution latency

### Structured Logging

All events logged as JSON:
- FIX connection status
- Scanner signals and opportunities
- Order placement and execution
- Risk management triggers
- Position updates

Example log:
```json
{
  "event": "scanner_signal",
  "symbol": "AAPL",
  "signal_type": "BREAKOUT_UP",
  "reason": "Price breakout: 2.5%",
  "price": 150.25,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## SEO: Who Is This Bot For?

This project is designed for people searching for:

- **DAS Trader bot**
- **DAS Trader automated trading**
- **DAS Trader FIX API bot**
- **Trading bot for DAS Trader**
- **DAS Trader scanner bot**
- **DAS Trader short selling bot**
- **Algorithmic trading DAS Trader**
- **DAS Trader risk management bot**

Perfect for:

- **Professional traders** using DAS Trader platform
- **Algorithmic traders** seeking automated execution
- **Day traders** needing fast order execution
- **Quantitative traders** implementing systematic strategies
- **Risk managers** requiring automated position monitoring

## Common Use Cases

### 1. Breakout Trading

Configure scanner to detect price breakouts:
```env
SCANNER__PRICE_BREAKOUT_THRESHOLD_PCT=2.0
EXECUTION__DEFAULT_ORDER_TYPE=MARKET
```

Bot automatically buys on upward breakouts and sells on downward breakouts.

### 2. Volume-Based Trading

Detect volume spikes and trade momentum:
```env
SCANNER__VOLUME_SPIKE_THRESHOLD=2.5
```

Bot identifies unusual volume activity and executes trades.

### 3. Short Selling Strategy

Enable short selling bot for bearish opportunities:
```env
SHORT_SELLING__ENABLED=true
SHORT_SELLING__SHORT_ENTRY_THRESHOLD_PCT=-1.5
```

Bot automatically shorts stocks on price drops.

### 4. Risk-Controlled Trading

Set strict risk limits:
```env
RISK__STOP_LOSS_PCT=1.0
RISK__MAX_DAILY_LOSS_USD=2000.0
RISK__MAX_POSITION_SIZE_USD=10000.0
```

Bot automatically manages risk with stop-losses and position limits.

## Troubleshooting

### FIX Connection Issues

- **Verify DAS Trader is running** and FIX API is enabled
- **Check network connectivity** to DAS Trader host/port
- **Verify credentials** in config file
- **Review FIX logs** in `log/` directory

### Order Execution Issues

- **Check account permissions** – Ensure trading permissions are enabled
- **Verify symbol format** – Use correct symbol format (e.g., "AAPL" not "AAPL.US")
- **Review order size limits** – Ensure orders don't exceed account limits
- **Check market hours** – Some orders may fail outside trading hours

### Scanner Not Detecting Opportunities

- **Adjust thresholds** – Lower breakout/volume thresholds if too strict
- **Check market data feed** – Ensure FIX connection is receiving market data
- **Verify symbol list** – Confirm symbols are actively traded
- **Review scan interval** – Increase scan interval if CPU usage is high

## Safety & Risk Management

⚠️ **Important:** This bot executes real trades with real money. Use with caution.

1. **Start with Paper Trading** – Test thoroughly before live trading
2. **Set Conservative Limits** – Use low position sizes and tight stop-losses initially
3. **Monitor Continuously** – Watch logs and metrics during initial runs
4. **Understand Risks** – Automated trading involves market risk and technical risk
5. **Comply with Regulations** – Ensure compliance with local trading regulations
6. **Backup Strategies** – Have manual override procedures ready

## License

Use at your own risk. Automated trading involves significant financial risk.  
Ensure compliance with DAS Trader terms of service and local regulations before using in production.

## Future Enhancements

- **Machine learning integration** – ML-based signal weighting and prediction
- **Multi-strategy support** – Run multiple strategies simultaneously
- **Backtesting framework** – Historical strategy performance testing
- **Portfolio optimization** – Cross-position risk management
- **Advanced order types** – Iceberg orders, TWAP, VWAP execution
- **Custom indicators** – Support for custom technical indicators

