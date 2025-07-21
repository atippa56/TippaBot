#!/bin/bash

# Trading Bot Test Script
# This script helps you test the trading bot in a safe environment

echo "🚀 Crypto Trading Bot - Test Runner"
echo "===================================="
echo ""

# Check if executables exist
if [ ! -f "build_test/trading_bot" ]; then
    echo "❌ Error: trading_bot executable not found!"
    echo "Please run: cd build_test && make"
    exit 1
fi

if [ ! -f "build_test/backtest_runner" ]; then
    echo "❌ Error: backtest_runner executable not found!"
    echo "Please run: cd build_test && make"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data web/static config

# Check if config file exists
if [ ! -f "config/trading_bot.json" ]; then
    echo "❌ Error: Configuration file config/trading_bot.json not found!"
    echo "Please create the configuration file first."
    exit 1
fi

echo "✅ Configuration file found"

# Show configuration summary
echo ""
echo "📋 Configuration Summary:"
echo "========================"
echo "• Mode: TESTNET (Safe for testing)"
echo "• Symbols: BTCUSDT, ETHUSDT"
echo "• Strategy: Momentum"
echo "• Trading: DISABLED"
echo "• Web Interface: http://localhost:8080"
echo "• Database: data/trading_bot.db"
echo "• Logs: logs/trading_bot.log"
echo ""

# Menu options
echo "Choose an option:"
echo "1. Run Trading Bot (Main Application)"
echo "2. Run Backtest Engine"
echo "3. View Configuration"
echo "4. Check System Status"
echo "5. Exit"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🤖 Starting Trading Bot..."
        echo "Web interface will be available at: http://localhost:8080"
        echo "Press Ctrl+C to stop the bot"
        echo ""
        ./build_test/trading_bot config/trading_bot.json
        ;;
    2)
        echo ""
        echo "📊 Starting Backtest Engine..."
        echo "This will run historical backtests on your strategies"
        echo ""
        ./build_test/backtest_runner
        ;;
    3)
        echo ""
        echo "⚙️ Current Configuration:"
        echo "========================"
        if [ -f "config/trading_bot.json" ]; then
            cat config/trading_bot.json | python -m json.tool 2>/dev/null || cat config/trading_bot.json
        else
            echo "Configuration file not found."
        fi
        ;;
    4)
        echo ""
        echo "🔍 System Status:"
        echo "================"
        echo "• Trading Bot: $([ -f build_test/trading_bot ] && echo "✅ Ready" || echo "❌ Not built")"
        echo "• Backtest Engine: $([ -f build_test/backtest_runner ] && echo "✅ Ready" || echo "❌ Not built")"
        echo "• Configuration: $([ -f config/trading_bot.json ] && echo "✅ Found" || echo "❌ Missing")"
        echo "• Logs Directory: $([ -d logs ] && echo "✅ Ready" || echo "❌ Missing")"
        echo "• Data Directory: $([ -d data ] && echo "✅ Ready" || echo "❌ Missing")"
        echo "• Web Directory: $([ -d web/static ] && echo "✅ Ready" || echo "❌ Missing")"
        echo ""
        echo "📊 Recent Logs:"
        if [ -f "logs/trading_bot.log" ]; then
            tail -10 logs/trading_bot.log
        else
            echo "No logs yet. Run the bot to generate logs."
        fi
        ;;
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid option. Please choose 1-5."
        exit 1
        ;;
esac 