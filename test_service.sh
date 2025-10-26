#!/bin/bash

echo "=== Order Service Test Script ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed"
    exit 1
fi

print_status "Python3 found: $(python3 --version)"

# Install dependencies
print_status "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi

# Run tests
print_status "Running unit tests..."
python3 -m pytest test_app.py -v

if [ $? -eq 0 ]; then
    print_status "All tests passed!"
else
    print_error "Some tests failed"
    exit 1
fi

# Test the API endpoints
print_status "Testing API endpoints..."

# Start the app in background
print_status "Starting the application..."
python3 app.py &
APP_PID=$!

# Wait for app to start
sleep 3

# Test health endpoint
print_status "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:5000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_status "Health check passed"
else
    print_error "Health check failed"
    kill $APP_PID
    exit 1
fi

# Test creating an order
print_status "Testing order creation..."
ORDER_RESPONSE=$(curl -s -X POST http://localhost:5000/orders \
    -H "Content-Type: application/json" \
    -d '{"customer_name": "Test User", "product_name": "Test Product", "quantity": 1, "price": 100.0}')

if echo "$ORDER_RESPONSE" | grep -q "Test User"; then
    print_status "Order creation test passed"
else
    print_error "Order creation test failed"
    kill $APP_PID
    exit 1
fi

# Test getting orders
print_status "Testing get orders..."
ORDERS_RESPONSE=$(curl -s http://localhost:5000/orders)
if echo "$ORDERS_RESPONSE" | grep -q "Test User"; then
    print_status "Get orders test passed"
else
    print_error "Get orders test failed"
    kill $APP_PID
    exit 1
fi

# Stop the app
kill $APP_PID

print_status "All tests completed successfully!"
print_status "Order service is ready for deployment!"
