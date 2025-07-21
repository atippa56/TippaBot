# 🚀 Production Deployment Guide

## Overview
This guide covers deploying the Enhanced Trading Bot for production use with real money trading.

## 🔒 Security First

### 1. Environment Setup
```bash
# Create production environment
python3 -m venv venv_prod
source venv_prod/bin/activate
pip install -r requirements.txt

# Install additional security packages
pip install python-dotenv cryptography
```

### 2. API Key Management
Create `.env` file (NEVER commit this):
```bash
# Exchange API Keys (for real trading)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# Optional: Coinbase Pro
COINBASE_API_KEY=your_coinbase_api_key_here
COINBASE_SECRET_KEY=your_coinbase_secret_key_here

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost/trading_bot

# Security
SECRET_KEY=your_random_secret_key_here
ENCRYPTION_KEY=your_32_byte_encryption_key

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
LOG_LEVEL=INFO
```

### 3. API Key Security Best Practices
- **Never store API keys in code**
- Use environment variables or secure key management
- Enable IP whitelisting on exchange accounts
- Use API keys with trading permissions only (no withdrawal)
- Regularly rotate API keys
- Monitor API usage and set rate limits

## 🏗️ Production Architecture

### Option 1: VPS/Cloud Server
```bash
# Ubuntu/Debian setup
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx supervisor

# Create application directory
sudo mkdir -p /opt/trading-bot
sudo chown $USER:$USER /opt/trading-bot
cd /opt/trading-bot

# Clone/copy application
git clone your-repo-url .
# or copy files manually

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 tradingbot
RUN chown -R tradingbot:tradingbot /app
USER tradingbot

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/status || exit 1

CMD ["python", "trading_bot.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  trading-bot:
    build: .
    ports:
      - "8080:8080"
    environment:
      - BINANCE_API_KEY=${BINANCE_API_KEY}
      - BINANCE_SECRET_KEY=${BINANCE_SECRET_KEY}
      - TRADING_MODE=LIVE
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - trading-bot
    restart: unless-stopped
```

### Option 3: AWS/GCP/Azure Cloud
- Use managed services for scalability
- Implement auto-scaling based on load
- Use managed databases (RDS, Cloud SQL)
- Implement proper monitoring and alerting

## 🔧 Production Configuration

### 1. Enhanced Trading Bot Configuration
```python
# production_config.py
import os
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    # Trading settings
    TRADING_MODE = 'LIVE'  # PAPER, TESTNET, LIVE
    RISK_PER_TRADE = 0.01  # 1% risk per trade (conservative)
    MAX_POSITIONS = 5      # Maximum concurrent positions
    STOP_LOSS_PERCENT = 0.05  # 5% stop loss
    
    # Exchange settings
    EXCHANGE = 'binance'   # binance, coinbase, etc.
    API_KEY = os.getenv('BINANCE_API_KEY')
    SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    
    # Monitoring
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Performance
    MAX_TRADES_HISTORY = 1000
    MARKET_DATA_CACHE_TTL = 30  # seconds
    TRADING_LOOP_INTERVAL = 60  # seconds
```

### 2. Database Setup (PostgreSQL)
```sql
-- Create database
CREATE DATABASE trading_bot;
CREATE USER trading_bot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE trading_bot TO trading_bot_user;

-- Create tables
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    pnl DECIMAL(20,8),
    exchange_order_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'executed'
);

CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20,8) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    current_price DECIMAL(20,8),
    unrealized_pnl DECIMAL(20,8),
    status VARCHAR(20) DEFAULT 'OPEN',
    exit_price DECIMAL(20,8),
    exit_time TIMESTAMP,
    realized_pnl DECIMAL(20,8)
);

CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_status ON positions(status);
```

### 3. Monitoring and Alerting
```python
# monitoring.py
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import smtplib
from email.mime.text import MIMEText

class ProductionMonitoring:
    def __init__(self):
        # Initialize Sentry for error tracking
        if os.getenv('SENTRY_DSN'):
            sentry_sdk.init(
                dsn=os.getenv('SENTRY_DSN'),
                integrations=[FlaskIntegration()],
                traces_sample_rate=1.0,
            )
        
        # Setup email alerts
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL'),
            'to_email': os.getenv('TO_EMAIL')
        }
    
    def send_alert(self, subject, message, level='INFO'):
        """Send email alert"""
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"[Trading Bot {level}] {subject}"
            msg['From'] = self.email_config['from_email']
            msg['To'] = self.email_config['to_email']
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
                
            logging.info(f"Alert sent: {subject}")
        except Exception as e:
            logging.error(f"Failed to send alert: {e}")
    
    def monitor_trading_performance(self, bot):
        """Monitor trading performance and send alerts"""
        # Check for large losses
        total_pnl = sum(p.realized_pnl or 0 for p in bot.positions.values())
        if total_pnl < -1000:  # Alert if loss > $1000
            self.send_alert(
                "Large Loss Detected",
                f"Trading bot has incurred a loss of ${abs(total_pnl):.2f}",
                "WARNING"
            )
        
        # Check for unusual trading activity
        recent_trades = len([t for t in bot.trades if (datetime.now() - t.timestamp).hours < 1])
        if recent_trades > 20:  # Alert if > 20 trades in 1 hour
            self.send_alert(
                "High Trading Activity",
                f"Bot has executed {recent_trades} trades in the last hour",
                "WARNING"
            )
```

## 🚀 Deployment Steps

### 1. Pre-deployment Checklist
- [ ] API keys configured and tested
- [ ] Database setup and tested
- [ ] Monitoring configured
- [ ] SSL certificates installed
- [ ] Firewall configured
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan ready

### 2. Deployment Commands
```bash
# Option 1: Direct deployment
cd /opt/trading-bot
source venv/bin/activate
python trading_bot.py

# Option 2: Using supervisor
sudo systemctl start trading-bot
sudo systemctl enable trading-bot

# Option 3: Docker deployment
docker-compose up -d
docker-compose logs -f trading-bot
```

### 3. Health Checks
```bash
# Check if bot is running
curl http://localhost:8080/api/status

# Check logs
tail -f logs/trading_bot.log

# Check database
psql -d trading_bot -c "SELECT COUNT(*) FROM trades;"

# Monitor system resources
htop
df -h
```

## 📊 Performance Optimization

### 1. Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_trades_symbol_timestamp ON trades(symbol, timestamp);
CREATE INDEX idx_positions_symbol_status ON positions(symbol, status);

-- Partition tables by date for large datasets
CREATE TABLE trades_2024 PARTITION OF trades
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### 2. Caching Strategy
```python
import redis
import json

class CacheManager:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
    
    def cache_market_data(self, symbol, data, ttl=30):
        """Cache market data for 30 seconds"""
        key = f"market_data:{symbol}"
        self.redis.setex(key, ttl, json.dumps(data))
    
    def get_cached_market_data(self, symbol):
        """Get cached market data"""
        key = f"market_data:{symbol}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
```

### 3. Load Balancing
```nginx
# nginx.conf
upstream trading_bot {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://trading_bot;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔄 Continuous Deployment

### 1. GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy Trading Bot

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.4
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.KEY }}
          script: |
            cd /opt/trading-bot
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart trading-bot
```

## 🛡️ Security Checklist

- [ ] API keys stored securely (environment variables)
- [ ] Database credentials encrypted
- [ ] SSL/TLS enabled for all connections
- [ ] Firewall configured (only necessary ports open)
- [ ] Regular security updates applied
- [ ] Access logs monitored
- [ ] Backup encryption enabled
- [ ] Two-factor authentication enabled where possible

## 📈 Scaling Considerations

### 1. Horizontal Scaling
- Multiple bot instances behind load balancer
- Database read replicas
- Redis cluster for caching
- Message queue for trade execution

### 2. Vertical Scaling
- Increase server resources (CPU, RAM)
- Optimize database queries
- Implement connection pooling
- Use CDN for static assets

## 🚨 Emergency Procedures

### 1. Stop Trading Immediately
```bash
# Emergency stop
curl -X POST http://localhost:8080/api/stop

# Kill process if needed
sudo systemctl stop trading-bot
# or
pkill -f trading_bot.py
```

### 2. Data Backup
```bash
# Backup database
pg_dump trading_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d_%H%M%S).tar.gz logs/
```

### 3. Rollback Procedure
```bash
# Revert to previous version
git checkout HEAD~1
sudo systemctl restart trading-bot

# Restore database if needed
psql trading_bot < backup_file.sql
```

## 📞 Support and Maintenance

### 1. Regular Maintenance Tasks
- Daily: Check logs for errors
- Weekly: Review trading performance
- Monthly: Update dependencies
- Quarterly: Security audit

### 2. Monitoring Dashboard
- Set up Grafana dashboard
- Monitor key metrics:
  - Trading performance
  - System resources
  - API response times
  - Error rates

### 3. Contact Information
- Emergency: [Your emergency contact]
- Technical support: [Your support email]
- Monitoring alerts: [Your alert email]

---

**⚠️ Important Disclaimer:**
This trading bot is for educational and demonstration purposes. Real money trading involves significant risk. Always:
- Start with small amounts
- Test thoroughly in paper trading mode
- Monitor the bot continuously
- Have emergency stop procedures ready
- Never invest more than you can afford to lose 