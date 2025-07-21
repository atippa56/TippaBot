#!/bin/bash

echo "🧪 COMPREHENSIVE TRADING BOT TEST SUITE"
echo "======================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_success="$3"
    
    echo -e "${BLUE}Testing: $test_name${NC}"
    
    # Run the test command
    response=$(eval "$test_command" 2>/dev/null)
    exit_code=$?
    
    # Check if the command succeeded
    if [ $exit_code -eq 0 ]; then
        # Check if response contains success indicator
        if echo "$response" | grep -q '"success":true' || echo "$response" | grep -q '"status":"success"' || [ "$expected_success" = "any" ]; then
            echo -e "${GREEN}✅ PASSED${NC}: $test_name"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            echo "   Response: $response"
        else
            echo -e "${RED}❌ FAILED${NC}: $test_name (Success not found in response)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            echo "   Response: $response"
        fi
    else
        echo -e "${RED}❌ FAILED${NC}: $test_name (Command failed with exit code $exit_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "   Response: $response"
    fi
    echo ""
}

# Check if bot is running
echo -e "${YELLOW}Checking if trading bot is running...${NC}"
if pgrep -f "minimal_bot" > /dev/null; then
    echo -e "${GREEN}✅ Trading bot is running${NC}"
else
    echo -e "${RED}❌ Trading bot is not running. Please start it first.${NC}"
    exit 1
fi
echo ""

# Test 1: Basic API Status
run_test "API Status Check" \
    'curl -s "http://localhost:8080/api/status"' \
    "true"

# Test 2: Market Data
run_test "Market Data API" \
    'curl -s "http://localhost:8080/api/market-data"' \
    "true"

# Test 3: Positions API
run_test "Positions API" \
    'curl -s "http://localhost:8080/api/positions"' \
    "true"

# Test 4: Trades API
run_test "Trades API" \
    'curl -s "http://localhost:8080/api/trades"' \
    "true"

# Test 5: Binance Connection Test
run_test "Binance Connection Test" \
    'curl -s "http://localhost:8080/api/test-connection"' \
    "true"

# Test 6: Account Balance
run_test "Account Balance API" \
    'curl -s "http://localhost:8080/api/balance"' \
    "true"

# Test 7: Start Trading
run_test "Start Trading" \
    'curl -X POST "http://localhost:8080/api/control" -H "Content-Type: application/json" -d '"'"'{"command": "start_trading"}'"'"' -s' \
    "true"

# Test 8: Test Trade (requires trading to be started)
run_test "Test Trade Placement" \
    'curl -X POST "http://localhost:8080/api/test-trade" -H "Content-Type: application/json" -d '"'"'{"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.001}'"'"' -s' \
    "true"

# Test 9: Stop Trading
run_test "Stop Trading" \
    'curl -X POST "http://localhost:8080/api/control" -H "Content-Type: application/json" -d '"'"'{"command": "stop_trading"}'"'"' -s' \
    "true"

# Test 10: Cryptocurrency Search
run_test "Cryptocurrency Search" \
    'curl -s "http://localhost:8080/api/search?query=bitcoin"' \
    "true"

# Test 11: Web Interface Accessibility
run_test "Web Interface" \
    'curl -s "http://localhost:8080/" | head -5' \
    "any"

# Test 12: Selected Cryptocurrencies
run_test "Selected Cryptocurrencies API" \
    'curl -s "http://localhost:8080/api/selected"' \
    "true"

echo ""
echo "🏁 TEST SUMMARY"
echo "==============="
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
echo -e "📊 Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Trading bot is fully functional.${NC}"
    echo ""
    echo "🌐 Web Interface: http://localhost:8080"
    echo "📊 Real-time market data: ✅ Active"
    echo "🔗 Binance testnet: ✅ Connected"
    echo "⚡ Trading controls: ✅ Working"
    echo "💰 Balance monitoring: ✅ Working"
    echo "🧪 Test trading: ✅ Working"
    echo "📈 Positions tracking: ✅ Working"
    echo "📋 Trade history: ✅ Working"
    echo ""
    echo -e "${YELLOW}🚀 Your trading bot is ready for testnet trading!${NC}"
else
    echo ""
    echo -e "${RED}⚠️  Some tests failed. Please check the errors above.${NC}"
    exit 1
fi 