# Order Service

Một order service đơn giản được viết bằng Flask để test deploy multi môi trường trên Jenkins.

## Tính năng

- **Health Check**: Endpoint `/health` để kiểm tra trạng thái service
- **CRUD Operations**: 
  - `GET /orders` - Lấy danh sách tất cả orders
  - `GET /orders/{id}` - Lấy order theo ID
  - `POST /orders` - Tạo order mới
  - `PUT /orders/{id}/status` - Cập nhật trạng thái order
  - `DELETE /orders/{id}` - Xóa order

## Cài đặt và chạy

### Local Development

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy tests
python -m pytest test_app.py -v

# Chạy ứng dụng
python app.py
```

### Docker

```bash
# Build image
docker build -t order-service .

# Chạy container
docker run -p 5000:5000 order-service
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Tạo Order
```bash
POST /orders
Content-Type: application/json

{
    "customer_name": "John Doe",
    "product_name": "Laptop",
    "quantity": 1,
    "price": 1000.0
}
```

### Lấy tất cả Orders
```bash
GET /orders
```

### Lấy Order theo ID
```bash
GET /orders/{order_id}
```

### Cập nhật trạng thái Order
```bash
PUT /orders/{order_id}/status
Content-Type: application/json

{
    "status": "processing"
}
```

### Xóa Order
```bash
DELETE /orders/{order_id}
```

## Multi-Environment Deployment

Service hỗ trợ deploy trên nhiều môi trường:

- **Development**: Port 5001
- **Staging**: Port 5002  
- **Production**: Port 5000

Mỗi môi trường có file cấu hình riêng:
- `env.development`
- `env.staging`
- `env.production`

## Jenkins Pipeline

Jenkinsfile được cấu hình để:
1. Chạy unit tests
2. Build Docker image
3. Deploy tự động theo branch:
   - `develop` → Development
   - `staging` → Staging
   - `main` → Production (cần confirm)

## Testing

```bash
# Chạy tất cả tests
python -m pytest test_app.py -v

# Chạy test với coverage
python -m pytest test_app.py --cov=app
```
