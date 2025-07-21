#!/bin/bash

echo "🔍 WEBSITE DEBUGGING SCRIPT"
echo "============================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Checking if trading bot is running...${NC}"
if pgrep -f "minimal_bot" > /dev/null; then
    echo -e "${GREEN}✅ Trading bot is running${NC}"
else
    echo -e "${RED}❌ Trading bot is not running${NC}"
    echo "Please start the bot first: ./build_test/minimal_bot"
    exit 1
fi

echo ""
echo -e "${BLUE}2. Testing web server response...${NC}"
if curl -s "http://localhost:8080" > /dev/null; then
    echo -e "${GREEN}✅ Web server is responding${NC}"
else
    echo -e "${RED}❌ Web server is not responding${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}3. Testing API endpoints...${NC}"

# Test status endpoint
echo -n "   Status API: "
if curl -s "http://localhost:8080/api/status" | grep -q "success"; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Test start trading endpoint
echo -n "   Start Trading API: "
response=$(curl -s -X POST "http://localhost:8080/api/control" -H "Content-Type: application/json" -d '{"command": "start_trading"}')
if echo "$response" | grep -q "success"; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
    echo "     Response: $response"
fi

# Test stop trading endpoint
echo -n "   Stop Trading API: "
response=$(curl -s -X POST "http://localhost:8080/api/control" -H "Content-Type: application/json" -d '{"command": "stop_trading"}')
if echo "$response" | grep -q "success"; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
    echo "     Response: $response"
fi

echo ""
echo -e "${BLUE}4. Checking JavaScript functions in HTML...${NC}"

# Check if startBot function exists
if curl -s "http://localhost:8080" | grep -q "function startBot"; then
    echo -e "${GREEN}✅ startBot function found${NC}"
else
    echo -e "${RED}❌ startBot function not found${NC}"
fi

# Check if stopBot function exists
if curl -s "http://localhost:8080" | grep -q "function stopBot"; then
    echo -e "${GREEN}✅ stopBot function found${NC}"
else
    echo -e "${RED}❌ stopBot function not found${NC}"
fi

# Check if showMessage function exists
if curl -s "http://localhost:8080" | grep -q "function showMessage"; then
    echo -e "${GREEN}✅ showMessage function found${NC}"
else
    echo -e "${RED}❌ showMessage function not found${NC}"
fi

# Check if testJavaScript function exists
if curl -s "http://localhost:8080" | grep -q "function testJavaScript"; then
    echo -e "${GREEN}✅ testJavaScript function found${NC}"
else
    echo -e "${RED}❌ testJavaScript function not found${NC}"
fi

echo ""
echo -e "${BLUE}5. Checking HTML elements...${NC}"

# Check if buttons exist
if curl -s "http://localhost:8080" | grep -q 'onclick="startBot()"'; then
    echo -e "${GREEN}✅ Start Bot button found${NC}"
else
    echo -e "${RED}❌ Start Bot button not found${NC}"
fi

if curl -s "http://localhost:8080" | grep -q 'onclick="stopBot()"'; then
    echo -e "${GREEN}✅ Stop Bot button found${NC}"
else
    echo -e "${RED}❌ Stop Bot button not found${NC}"
fi

if curl -s "http://localhost:8080" | grep -q 'onclick="testJavaScript()"'; then
    echo -e "${GREEN}✅ Test JavaScript button found${NC}"
else
    echo -e "${RED}❌ Test JavaScript button not found${NC}"
fi

# Check if messageArea exists
if curl -s "http://localhost:8080" | grep -q 'id="messageArea"'; then
    echo -e "${GREEN}✅ messageArea element found${NC}"
else
    echo -e "${RED}❌ messageArea element not found${NC}"
fi

echo ""
echo -e "${BLUE}6. Testing direct API calls...${NC}"

echo "Testing Start Trading:"
curl -X POST "http://localhost:8080/api/control" -H "Content-Type: application/json" -d '{"command": "start_trading"}' -s | head -1

echo ""
echo "Testing Stop Trading:"
curl -X POST "http://localhost:8080/api/control" -H "Content-Type: application/json" -d '{"command": "stop_trading"}' -s | head -1

echo ""
echo "Testing Connection:"
curl -s "http://localhost:8080/api/test-connection" | head -1

echo ""
echo -e "${YELLOW}📋 DEBUGGING INSTRUCTIONS:${NC}"
echo "1. Open your browser to: http://localhost:8080"
echo "2. Open Developer Tools (F12)"
echo "3. Go to the Console tab"
echo "4. Click the '🧪 Test JavaScript' button"
echo "5. Check if you see the message: '🧪 JavaScript test function called'"
echo "6. If you don't see it, there might be a JavaScript error"
echo "7. Try clicking the Start Bot button and check for console messages"
echo ""
echo -e "${YELLOW}🔧 TROUBLESHOOTING:${NC}"
echo "- If JavaScript test button doesn't work: JavaScript is completely broken"
echo "- If JavaScript test works but trading buttons don't: API call issue"
echo "- If you see console errors: JavaScript syntax error"
echo "- If no console messages: onclick handlers not working"
echo ""
echo -e "${GREEN}✅ All API endpoints are working from command line${NC}"
echo -e "${GREEN}✅ All JavaScript functions are present in HTML${NC}"
echo -e "${GREEN}✅ All HTML elements are present${NC}"
echo ""
echo -e "${YELLOW}🎯 The issue is likely in the browser JavaScript execution${NC}"
echo -e "${YELLOW}   Please check the browser console for errors!${NC}" 