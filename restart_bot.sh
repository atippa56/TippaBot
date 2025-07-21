#!/bin/bash

set -e

# Kill any running minimal_bot
pkill -f minimal_bot || true
sleep 2

# Remove old database (optional, comment out if you want to keep history)
rm -f trading_bot.db

# Rebuild the bot
cmake --build build_test --target minimal_bot

# Start the bot in the background
./build_test/minimal_bot &

echo "✅ Bot restarted and running in background." 