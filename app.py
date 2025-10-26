from flask import Flask, request, jsonify
import os
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv()
environment = os.getenv('ENVIRONMENT')
app = Flask(__name__)

# Simple in-memory storage for demo purposes
orders = {}

class Order:
    def __init__(self, customer_name, product_name, quantity, price):
        self.id = str(uuid.uuid4())
        self.customer_name = customer_name
        self.product_name = product_name
        self.quantity = quantity
        self.price = price
        self.total = quantity * price
        self.status = "pending"
        self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "price": self.price,
            "total": self.total,
            "status": self.status,
            "created_at": self.created_at
        }

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({"message": f"Welcome to the Order Service environment {environment}!"})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "order-service",
        "environment": os.getenv('ENVIRONMENT', 'development')
    })

@app.route('/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
    return jsonify({
        "orders": [order.to_dict() for order in orders.values()],
        "count": len(orders)
    })

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get a specific order by ID"""
    if order_id not in orders:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(orders[order_id].to_dict())

@app.route('/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['customer_name', 'product_name', 'quantity', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Validate data types
        if not isinstance(data['quantity'], int) or data['quantity'] <= 0:
            return jsonify({"error": "Quantity must be a positive integer"}), 400

        if not isinstance(data['price'], (int, float)) or data['price'] <= 0:
            return jsonify({"error": "Price must be a positive number"}), 400

        # Create order
        order = Order(
            customer_name=data['customer_name'],
            product_name=data['product_name'],
            quantity=data['quantity'],
            price=data['price']
        )

        orders[order.id] = order

        return jsonify(order.to_dict()), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    if order_id not in orders:
        return jsonify({"error": "Order not found"}), 404

    data = request.get_json()
    if 'status' not in data:
        return jsonify({"error": "Missing status field"}), 400

    valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    if data['status'] not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 400

    orders[order_id].status = data['status']
    return jsonify(orders[order_id].to_dict())

@app.route('/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Delete an order"""
    if order_id not in orders:
        return jsonify({"error": "Order not found"}), 404

    del orders[order_id]
    return jsonify({"message": "Order deleted successfully"})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('ENVIRONMENT', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
