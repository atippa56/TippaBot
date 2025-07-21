# 🚀 Enhanced Trading Bot

A complete, production-ready cryptocurrency trading bot with real-time market data, advanced trading strategies, and a modern web dashboard.

## ✨ Enhanced Features

### 🎯 **Real Trading Logic**
- **Real Market Data**: Live prices from CoinGecko API (no fake data!)
- **Advanced Strategies**: Mean reversion (Bollinger Bands) and momentum (MA crossover)
- **Position Management**: Proper OPEN/CLOSED status tracking
- **Risk Management**: 2% risk per trade with position sizing
- **Real PnL Tracking**: Unrealized and realized profit/loss calculation

### 🎨 **Modern Dashboard**
- **Tabbed Interface**: Market Data, Positions, Trades, Custom Cryptos
- **Real-time Updates**: Auto-refresh every 5 seconds
- **Status Tracking**: Clear OPEN/CLOSED position indicators
- **Trade History**: Limited to last 50 trades for performance
- **Responsive Design**: Works on desktop and mobile

### ⚙️ **Crypto Customization**
- **Add/Remove Cryptocurrencies**: Search and manage your watchlist
- **1000+ Available Cryptos**: Full CoinGecko database integration
- **Dynamic Updates**: Changes apply immediately
- **Performance Optimized**: Limits to 10 active cryptos for speed

### 🔒 **Production Ready**
- **Multiple Trading Modes**: PAPER, TESTNET, LIVE
- **Security Best Practices**: Environment variables, API key management
- **Comprehensive Logging**: Detailed trade and system logs
- **Error Handling**: Robust error recovery and monitoring
- **Deployment Ready**: Docker, VPS, and cloud deployment guides

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │  Trading Engine │    │  Market Data    │
│                 │    │                 │    │                 │
│ • Real-time UI  │◄──►│ • Strategies    │◄──►│ • CoinGecko API │
│ • Tab Interface │    │ • Risk Mgmt     │    │ • Live Prices   │
│ • Custom Cryptos│    │ • Position Mgmt │    │ • 24h Changes   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask Server  │    │   Trade Log     │    │   Position DB   │
│                 │    │                 │    │                 │
│ • REST API      │    │ • Trade History │    │ • Open/Closed   │
│ • Web Interface │    │ • PnL Tracking  │    │ • Entry/Exit    │
│ • Real-time     │    │ • Performance   │    │ • Risk Metrics  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Bot
```bash
python3 trading_bot.py
```

### 3. Access Dashboard
Open your browser to: **http://localhost:8080**

### 4. Start Trading
Click "🚀 Start Trading" in the dashboard

## 📊 Dashboard Features

### Market Data Tab
- Live cryptocurrency prices
- 24-hour price changes
- Volume and market cap data
- Real-time updates every 30 seconds

### Positions Tab
- **OPEN Positions**: Currently held positions with unrealized PnL
- **CLOSED Positions**: Completed trades with realized PnL
- Entry/exit prices and timestamps
- Position status indicators

### Recent Trades Tab
- Last 50 executed trades
- Buy/sell actions with prices
- Strategy used for each trade
- PnL for completed trades

### Custom Cryptos Tab
- **Current Watchlist**: Manage your selected cryptocurrencies
- **Search & Add**: Find and add new cryptos from 1000+ options
- **Remove**: Remove cryptos from your watchlist
- **Real-time Updates**: Changes apply immediately

## 🔧 Configuration

### Trading Parameters
```python
# Risk Management
RISK_PER_TRADE = 0.02  # 2% risk per trade
MAX_POSITIONS = 5      # Maximum concurrent positions

# Strategy Settings
BOLLINGER_PERIOD = 20  # Bollinger Bands period
BOLLINGER_STD = 2      # Standard deviation multiplier
MA_SHORT = 10          # Short moving average
MA_LONG = 30           # Long moving average

# Performance
MAX_TRADES_HISTORY = 50  # Limit recent trades display
TRADING_LOOP_INTERVAL = 30  # Analysis frequency (seconds)
```

### Environment Variables
```bash
# Trading Mode
TRADING_MODE=PAPER  # PAPER, TESTNET, LIVE

# Exchange API Keys (for real trading)
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/trading_bot
```

## 📈 Trading Strategies

### 1. Momentum Strategy
- **Buy Signal**: 24h price change > +2%
- **Sell Signal**: 24h price change < -1%
- **Risk**: 2% of balance per trade
- **Position**: Long only

### 2. Mean Reversion (Bollinger Bands)
- **Buy Signal**: Price below lower Bollinger Band
- **Sell Signal**: Price above upper Bollinger Band
- **Risk Management**: Stop loss at 5%

### 3. Moving Average Crossover
- **Buy Signal**: Fast MA crosses above slow MA
- **Sell Signal**: Fast MA crosses below slow MA
- **Confirmation**: Volume increase

## 🔒 Production Deployment

### Security Checklist
- [ ] API keys stored in environment variables
- [ ] SSL/TLS enabled for all connections
- [ ] Firewall configured (ports 80, 443, 8080)
- [ ] Database credentials encrypted
- [ ] Regular security updates
- [ ] Monitoring and alerting setup

### Deployment Options
1. **VPS/Cloud Server**: Direct deployment with nginx
2. **Docker**: Containerized deployment with docker-compose
3. **Cloud Platforms**: AWS, GCP, Azure with managed services

See `DEPLOYMENT_GUIDE.md` for detailed production setup instructions.

## 📊 Performance Metrics

### Real-time Monitoring
- **Trading Performance**: Total PnL, win rate, Sharpe ratio
- **System Health**: API response times, error rates
- **Risk Metrics**: Maximum drawdown, position exposure
- **Market Data**: Data freshness, API limits

### Key Indicators
- **Balance**: Current account balance
- **Open Positions**: Number of active trades
- **Total PnL**: Cumulative profit/loss
- **Total Trades**: Number of executed trades
- **Trading Mode**: PAPER/TESTNET/LIVE status

## 🛠️ API Endpoints

### Core Endpoints
- `GET /api/status` - Bot status and metrics
- `GET /api/market_data` - Live market data
- `GET /api/positions` - Current positions
- `GET /api/trades` - Recent trades (last 50)

### Control Endpoints
- `POST /api/start` - Start trading
- `POST /api/stop` - Stop trading

### Customization Endpoints
- `GET /api/custom_cryptos` - Get custom crypto list
- `POST /api/custom_cryptos/add` - Add cryptocurrency
- `POST /api/custom_cryptos/remove` - Remove cryptocurrency

## 🔍 Troubleshooting

### Common Issues
1. **Port Conflicts**: Change port in `trading_bot.py`
2. **API Rate Limits**: Increase intervals in configuration
3. **Data Not Loading**: Check internet connection and CoinGecko API
4. **Trades Not Executing**: Verify trading mode and balance

### Logs
- **Application Logs**: `trading_bot.log`
- **Web Server Logs**: Flask built-in logging
- **Error Tracking**: Check logs for detailed error messages

## 📚 Advanced Features

### Database Integration
- PostgreSQL support for production
- Trade and position persistence
- Performance analytics
- Historical data analysis

### Monitoring & Alerting
- Email alerts for large losses
- High trading activity warnings
- System health monitoring
- Performance dashboards

### Scalability
- Horizontal scaling with load balancers
- Database read replicas
- Redis caching for market data
- Message queues for trade execution

## ⚠️ Important Disclaimers

### Risk Warning
- **Cryptocurrency trading is highly risky**
- **Never invest more than you can afford to lose**
- **Past performance does not guarantee future results**
- **Always test thoroughly in paper trading mode first**

### Legal Compliance
- **Check local regulations before trading**
- **Ensure compliance with tax laws**
- **Verify exchange terms of service**
- **Consider consulting a financial advisor**

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add type hints for functions
- Include docstrings for classes/methods
- Write unit tests for new features

## 📞 Support

### Documentation
- **User Guide**: This README
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **API Documentation**: Inline code comments

### Issues & Questions
- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share ideas
- **Wiki**: Additional documentation and tutorials

---

**🎉 Ready to start trading? Launch the bot and explore the enhanced dashboard!** 

## Production Deployment & Environment Setup

1. Copy `.env.example` to `.env` and fill in your Binance API credentials and admin password.
2. Set `TRADING_ENABLED=false` for display-only mode, or `true` to enable real trading.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the bot:
   ```bash
   python3 trading_bot.py
   ```

For Docker deployment, see the Docker section below (to be added). 

## Dockerized Deployment (Production-Ready)

1. **Clone the repository and set up your .env file:**
   - Copy `.env.example` to `.env` and fill in your Binance API keys, admin password, and (optionally) change the database URL.

2. **Build and start the stack:**
   ```bash
   docker-compose up --build
   ```
   This will start both the trading bot and a PostgreSQL database. The bot will be available at http://localhost:8080.

3. **Persistent Data:**
   - All trades, positions, and balance are stored in PostgreSQL and will persist across restarts.
   - The database volume is managed by Docker Compose (`pgdata`).

4. **Environment Variables:**
   - `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `ADMIN_PASSWORD`, `TRADING_ENABLED`, `DATABASE_URL`
   - Example for PostgreSQL: `DATABASE_URL=postgresql://tradinguser:strongpassword@db:5432/trading`

5. **Updating the App:**
   - Make code changes, then run `docker-compose up --build` again to redeploy.

6. **Stopping the App:**
   ```bash
   docker-compose down
   ```

## Notes
- Never commit your `.env` file with real secrets to GitHub.
- For production, use strong passwords and restrict dashboard access. 