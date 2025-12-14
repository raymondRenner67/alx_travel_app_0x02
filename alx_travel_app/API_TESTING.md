# API Testing Examples

## Using cURL

### 1. Create a Booking
```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "listing": 1,
    "check_in_date": "2025-12-20",
    "check_out_date": "2025-12-23",
    "number_of_guests": 2,
    "user_email": "user@example.com",
    "user_phone": "+251911223344"
  }'
```

### 2. Initiate Payment
```bash
curl -X POST http://localhost:8000/api/payments/initiate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "booking_id": 1,
    "return_url": "http://localhost:3000/payment/success"
  }'
```

### 3. Verify Payment
```bash
curl -X POST http://localhost:8000/api/payments/verify/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "transaction_id": "TXN-abc123-def456"
  }'
```

### 4. Get Payment Details
```bash
curl -X GET http://localhost:8000/api/payments/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### 5. List User Payments
```bash
curl -X GET http://localhost:8000/api/payments/ \
  -H "Authorization: Token YOUR_TOKEN"
```

## Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000/api"
TOKEN = "your-auth-token"
HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

# Create booking
booking_data = {
    "listing": 1,
    "check_in_date": "2025-12-20",
    "check_out_date": "2025-12-23",
    "number_of_guests": 2,
    "user_email": "user@example.com",
    "user_phone": "+251911223344"
}
response = requests.post(f"{BASE_URL}/bookings/", json=booking_data, headers=HEADERS)
booking = response.json()
print(f"Booking created: {booking['booking_reference']}")

# Initiate payment
payment_data = {
    "booking_id": booking["id"],
    "return_url": "http://localhost:3000/payment/success"
}
response = requests.post(f"{BASE_URL}/payments/initiate/", json=payment_data, headers=HEADERS)
payment = response.json()
print(f"Payment URL: {payment['payment_url']}")
print(f"Transaction ID: {payment['transaction_id']}")

# Verify payment (after user completes payment)
verify_data = {
    "transaction_id": payment["transaction_id"]
}
response = requests.post(f"{BASE_URL}/payments/verify/", json=verify_data, headers=HEADERS)
result = response.json()
print(f"Payment status: {result['status']}")
```

## Using Postman

### Import Collection

Create a new Postman collection with these requests:

1. **Create Booking**
   - Method: POST
   - URL: `{{base_url}}/bookings/`
   - Body: JSON (see above)

2. **Initiate Payment**
   - Method: POST
   - URL: `{{base_url}}/payments/initiate/`
   - Body: JSON (see above)

3. **Verify Payment**
   - Method: POST
   - URL: `{{base_url}}/payments/verify/`
   - Body: JSON (see above)

### Environment Variables
- `base_url`: http://localhost:8000/api
- `token`: your-auth-token

## Testing Scenarios

### Scenario 1: Successful Payment Flow
1. Create booking → 201 Created
2. Initiate payment → 201 Created (get payment_url)
3. Complete payment on Chapa
4. Verify payment → 200 OK (status: completed)
5. Check booking status → confirmed

### Scenario 2: Payment Already Completed
1. Create booking
2. Initiate payment
3. Complete payment
4. Try to initiate again → 400 Bad Request

### Scenario 3: Invalid Booking
1. Initiate payment with invalid booking_id → 404 Not Found

### Scenario 4: Verification Without Payment
1. Verify non-existent transaction → 404 Not Found

## Expected Responses

### Successful Payment Initiation
```json
{
  "success": true,
  "message": "Payment initiated successfully",
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "payment_url": "https://checkout.chapa.co/checkout/payment/...",
  "transaction_id": "TXN-a1b2c3-12345678",
  "amount": "3000.00",
  "currency": "ETB",
  "status": "pending"
}
```

### Successful Payment Verification
```json
{
  "success": true,
  "message": "Payment verified successfully",
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "amount": "3000.00",
  "booking_reference": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "booking_status": "confirmed",
  "completed_at": "2025-12-14T10:30:00Z"
}
```

### Payment Failure
```json
{
  "success": false,
  "message": "Payment verification failed",
  "error": "Transaction not found or expired",
  "status": "failed"
}
```
