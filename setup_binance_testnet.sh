#!/bin/bash

echo "🚀 Binance Testnet Setup Script"
echo "==============================="
echo ""

# Check if config file exists
if [ ! -f "config/binance_testnet.json" ]; then
    echo "❌ Config file not found: config/binance_testnet.json"
    echo "Please run cmake to build the project first."
    exit 1
fi

echo "📋 Follow these steps to set up Binance Testnet:"
echo ""
echo "1. Go to https://testnet.binance.vision/"
echo "2. Click 'Login with GitHub' and authorize the application"
echo "3. In the testnet dashboard, click 'API Keys' on the left"
echo "4. Click 'Create API Key' and give it a name (e.g., 'Trading Bot Test')"
echo "5. Copy the API Key and Secret Key"
echo ""

# Ask for API credentials
read -p "Enter your Binance Testnet API Key: " API_KEY
read -p "Enter your Binance Testnet Secret Key: " SECRET_KEY

if [ -z "$API_KEY" ] || [ -z "$SECRET_KEY" ]; then
    echo "❌ API Key and Secret Key cannot be empty"
    exit 1
fi

# Update the config file
echo "📝 Updating config/binance_testnet.json with your credentials..."

# Create a temporary file with the updated config
cat > config/binance_testnet.json << EOF
{
  "exchange": {
    "name": "binance_testnet",
    "api_key": "$API_KEY",
    "secret_key": "$SECRET_KEY",
    "base_url": "https://testnet.binance.vision",
    "ws_url": "wss://testnet-dstream.binance.vision/ws/"
  },
  "trading": {
    "mode": "TESTNET",
    "initial_balance": 10000.0,
    "default_trade_amount": 100.0,
    "max_position_size": 0.1,
    "max_daily_loss": 0.05,
    "stop_loss_percentage": 0.02,
    "take_profit_percentage": 0.04
  },
  "symbols": [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "ADAUSDT",
    "SOLUSDT",
    "DOTUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "LINKUSDT"
  ],
  "risk_management": {
    "max_trades_per_day": 50,
    "max_concurrent_positions": 5,
    "position_size_percentage": 0.02,
    "emergency_stop_loss": 0.10
  }
}
EOF

echo "✅ Configuration updated successfully!"
echo ""
echo "🔧 Next steps:"
echo "1. Build the project: cmake --build build_test"
echo "2. Test the connection: ./build_test/binance_test"
echo "3. If the test passes, you can start trading on testnet!"
echo ""
echo "⚠️  Important notes:"
echo "• This is TESTNET - no real money is involved"
echo "• Testnet accounts start with fake balances"
echo "• All trades are simulated but use real market data"
echo "• Perfect for testing strategies safely"
echo ""
echo "🎉 Setup complete! Happy testing!" 