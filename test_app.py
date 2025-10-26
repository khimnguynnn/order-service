import pytest
import json
from app import app, Order, orders

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def clear_orders():
    """Clear orders before each test"""
    orders.clear()
    yield
    orders.clear()

class TestOrderModel:
    """Test Order model"""
    
    def test_order_creation(self):
        """Test order creation with valid data"""
        order = Order("John Doe", "Laptop", 1, 1000.0)
        
        assert order.customer_name == "John Doe"
        assert order.product_name == "Laptop"
        assert order.quantity == 1
        assert order.price == 1000.0
        assert order.total == 1000.0
        assert order.status == "pending"
        assert order.id is not None
        assert order.created_at is not None
    
    def test_order_total_calculation(self):
        """Test total calculation"""
        order = Order("Jane Doe", "Phone", 2, 500.0)
        assert order.total == 1000.0

class TestOrderAPI:
    """Test Order API endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'order-service'
    
    def test_get_orders_empty(self, client, clear_orders):
        """Test getting orders when none exist"""
        response = client.get('/orders')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['orders'] == []
        assert data['count'] == 0
    
    def test_create_order_success(self, client, clear_orders):
        """Test creating a valid order"""
        order_data = {
            "customer_name": "John Doe",
            "product_name": "Laptop",
            "quantity": 1,
            "price": 1000.0
        }
        
        response = client.post('/orders', 
                             data=json.dumps(order_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['customer_name'] == "John Doe"
        assert data['product_name'] == "Laptop"
        assert data['quantity'] == 1
        assert data['price'] == 1000.0
        assert data['total'] == 1000.0
        assert data['status'] == "pending"
        assert 'id' in data
        assert 'created_at' in data
    
    def test_create_order_missing_field(self, client, clear_orders):
        """Test creating order with missing required field"""
        order_data = {
            "customer_name": "John Doe",
            "product_name": "Laptop",
            "quantity": 1
            # Missing price field
        }
        
        response = client.post('/orders',
                             data=json.dumps(order_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Missing required field' in data['error']
    
    def test_create_order_invalid_quantity(self, client, clear_orders):
        """Test creating order with invalid quantity"""
        order_data = {
            "customer_name": "John Doe",
            "product_name": "Laptop",
            "quantity": -1,
            "price": 1000.0
        }
        
        response = client.post('/orders',
                             data=json.dumps(order_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Quantity must be a positive integer' in data['error']
    
    def test_create_order_invalid_price(self, client, clear_orders):
        """Test creating order with invalid price"""
        order_data = {
            "customer_name": "John Doe",
            "product_name": "Laptop",
            "quantity": 1,
            "price": -100.0
        }
        
        response = client.post('/orders',
                             data=json.dumps(order_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Price must be a positive number' in data['error']
    
    def test_get_order_by_id(self, client, clear_orders):
        """Test getting a specific order by ID"""
        # First create an order
        order_data = {
            "customer_name": "John Doe",
            "product_name": "Laptop",
            "quantity": 1,
            "price": 1000.0
        }
        
        create_response = client.post('/orders',
                                    data=json.dumps(order_data),
                                    content_type='application/json')
        assert create_response.status_code == 201
        
        created_order = json.loads(create_response.data)
        order_id = created_order['id']
        
        # Now get the order by ID
        response = client.get(f'/orders/{order_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['id'] == order_id
        assert data['customer_name'] == "John Doe"
    
    def test_get_order_not_found(self, client, clear_orders):
        """Test getting a non-existent order"""
        response = client.get('/orders/non-existent-id')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Order not found' in data['error']
    
    def test_update_order_status(self, client, clear_orders):
        """Test updating order status"""
        # First create an order
        order_data = {
            "customer_name": "John Doe",
            "product_name": "Laptop",
            "quantity": 1,
            "price": 1000.0
        }
        
        create_response = client.post('/orders',
                                    data=json.dumps(order_data),
                                    content_type='application/json')
        created_order = json.loads(create_response.data)
        order_id = created_order['id']
        
        # Update status
        status_data = {"status": "processing"}
        response = client.put(f'/orders/{order_id}/status',
                             data=json.dumps(status_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == "processing"
    
    def test_update_order_status_invalid(self, client, clear_orders):
        """Test updating order status with invalid status"""
        # First create an order
        order_data = {
            "customer_name": "John Doe",
            "product_name": "Laptop",
            "quantity": 1,
            "price": 1000.0
        }
        
        create_response = client.post('/orders',
                                    data=json.dumps(order_data),
                                    content_type='application/json')
        created_order = json.loads(create_response.data)
        order_id = created_order['id']
        
        # Update with invalid status
        status_data = {"status": "invalid_status"}
        response = client.put(f'/orders/{order_id}/status',
                             data=json.dumps(status_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid status' in data['error']
    
    def test_delete_order(self, client, clear_orders):
        """Test deleting an order"""
        # First create an order
        order_data = {
            "customer_name": "John Doe",
            "product_name": "Laptop",
            "quantity": 1,
            "price": 1000.0
        }
        
        create_response = client.post('/orders',
                                    data=json.dumps(order_data),
                                    content_type='application/json')
        created_order = json.loads(create_response.data)
        order_id = created_order['id']
        
        # Delete the order
        response = client.delete(f'/orders/{order_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'message' in data
        assert 'deleted successfully' in data['message']
        
        # Verify order is deleted
        get_response = client.get(f'/orders/{order_id}')
        assert get_response.status_code == 404
    
    def test_delete_order_not_found(self, client, clear_orders):
        """Test deleting a non-existent order"""
        response = client.delete('/orders/non-existent-id')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Order not found' in data['error']
