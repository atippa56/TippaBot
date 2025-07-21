#!/bin/bash

set -e

# Check if minimal_bot is running
if pgrep -f minimal_bot > /dev/null; then
  echo "✅ minimal_bot is running"
else
  echo "❌ minimal_bot is NOT running"
fi

# Check if web server is up
if curl -s http://localhost:8080 > /dev/null; then
  echo "✅ Web server is responding on port 8080"
else
  echo "❌ Web server is NOT responding on port 8080"
fi

# Check for errors in logs
if grep -i 'error' logs/trading_bot.log | tail -10; then
  echo "⚠️  Errors found in logs above."
else
  echo "✅ No errors found in logs."
fi 