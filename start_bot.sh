#!/bin/bash

echo "🚀 Starting Clean Trading Bot"
echo "=============================="

# Kill any existing processes
echo "🛑 Stopping any existing processes..."
pkill -f "trading_bot.py" 2>/dev/null || true
sleep 2

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Create logs directory
mkdir -p logs

# Start the trading bot
echo "🚀 Starting trading bot..."
echo "🌐 Dashboard will be available at: http://localhost:5000"
echo "📝 Logs will be saved to: trading_bot.log"
echo ""
echo "Press Ctrl+C to stop the bot"
echo "=============================="

python3 trading_bot.py 