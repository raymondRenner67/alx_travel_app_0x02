# ALX Travel App - Chapa Payment Integration

A Django-based travel booking application with integrated Chapa payment processing. This project enables users to make secure bookings with payment verification through the Chapa API.

## Features

- **Travel Listings Management**: Browse and manage travel listings/properties
- **Booking System**: Create and manage bookings with date validation
- **Chapa Payment Integration**: Secure payment processing through Chapa API
- **Payment Verification**: Automatic and manual payment verification
- **Email Notifications**: Asynchronous email notifications using Celery
- **Webhook Support**: Real-time payment status updates via Chapa webhooks
- **RESTful API**: Complete REST API with Django REST Framework

## Project Structure

```
alx_travel_app/
├── alx_travel_app/          # Main project directory
│   ├── __init__.py
│   ├── settings.py          # Django settings with Chapa configuration
│   ├── urls.py              # Main URL configuration
│   ├── celery.py            # Celery configuration
│   ├── wsgi.py
│   └── asgi.py
├── listings/                # Listings app
│   ├── models.py            # Listing, Booking, and Payment models
│   ├── views.py             # API views for payments and bookings
│   ├── serializers.py       # DRF serializers
│   ├── services.py          # Chapa API integration service
│   ├── tasks.py             # Celery tasks for email notifications
│   ├── urls.py              # App URL configuration
│   ├── admin.py             # Django admin configuration
│   ├── signals.py           # Django signals
│   └── tests.py             # Unit tests
├── manage.py
├── requirements.txt
├── .env.example
└── .gitignore
```

## Models

### Listing
- Travel property/listing information
- Fields: title, description, location, price_per_night, available

### Booking
- User bookings with date ranges and guest information
- Fields: booking_reference (UUID), user, listing, check_in_date, check_out_date, number_of_guests, total_amount, status

### Payment
- Payment transaction records linked to bookings
- Fields: payment_id (UUID), booking, transaction_id, chapa_reference, amount, currency, status, payment_url, payment_response, verification_response

## Setup Instructions

### Prerequisites

- Python 3.8+
- Redis (for Celery)
- Chapa API account (https://developer.chapa.co/)

### Installation

1. **Clone the repository**
   ```bash
   cd alx_travel_app_0x02/alx_travel_app
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your configuration:
   ```
   DJANGO_SECRET_KEY=your-secret-key
   DEBUG=True
   CHAPA_SECRET_KEY=your-chapa-secret-key-here
   CHAPA_WEBHOOK_SECRET=your-webhook-secret
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Redis (in a separate terminal)**
   ```bash
   redis-server
   ```

8. **Start Celery worker (in a separate terminal)**
   ```bash
   celery -A alx_travel_app worker -l info
   ```

9. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Chapa API Setup

### 1. Create Chapa Account
- Visit https://dashboard.chapa.co/
- Sign up for a developer account
- Navigate to Settings > API Keys

### 2. Get API Credentials
- Copy your **Secret Key** (starts with `CHASECK-`)
- For testing, use the **Test Mode** keys
- For production, use **Live Mode** keys

### 3. Configure Webhook (Optional)
- In Chapa Dashboard, go to Settings > Webhooks
- Add webhook URL: `https://yourdomain.com/api/payments/webhook/`
- Copy the webhook secret

### 4. Test Mode vs Production
- **Test Mode**: Use test keys for development
  - Test cards available in Chapa documentation
  - No real money transactions
- **Production Mode**: Use live keys for real transactions
  - Real payment processing
  - Requires business verification

## API Endpoints

### Authentication
Most endpoints require authentication. Use Django session authentication or add token authentication as needed.

### Listings
- `GET /api/listings/` - List all listings
- `POST /api/listings/` - Create a listing (admin)
- `GET /api/listings/{id}/` - Get listing details
- `GET /api/listings/{id}/availability/` - Check listing availability

### Bookings
- `GET /api/bookings/` - List user's bookings
- `POST /api/bookings/` - Create a new booking
- `GET /api/bookings/{id}/` - Get booking details
- `GET /api/bookings/{id}/payment_status/` - Check payment status

### Payments

#### Initiate Payment
```http
POST /api/payments/initiate/
Content-Type: application/json
Authorization: Token <your-token>

{
  "booking_id": 1,
  "return_url": "http://localhost:3000/payment/success",
  "callback_url": "http://yourdomain.com/api/payments/webhook/"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Payment initiated successfully",
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "payment_url": "https://checkout.chapa.co/...",
  "transaction_id": "TXN-...",
  "amount": "3000.00",
  "currency": "ETB",
  "status": "pending"
}
```

#### Verify Payment
```http
POST /api/payments/verify/
Content-Type: application/json
Authorization: Token <your-token>

{
  "transaction_id": "TXN-..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Payment verified successfully",
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "amount": "3000.00",
  "booking_reference": "a1b2c3d4-...",
  "booking_status": "confirmed",
  "completed_at": "2025-12-14T10:30:00Z"
}
```

#### Webhook Endpoint
```http
POST /api/payments/webhook/
Content-Type: application/json

{
  "tx_ref": "TXN-...",
  "status": "success",
  "amount": "3000.00"
}
```

#### Get Payment Details
```http
GET /api/payments/{payment_id}/
Authorization: Token <your-token>
```

#### List User Payments
```http
GET /api/payments/
Authorization: Token <your-token>
```

## Payment Workflow

### 1. Create Booking
```python
# User creates a booking
POST /api/bookings/
{
  "listing": 1,
  "check_in_date": "2025-12-20",
  "check_out_date": "2025-12-23",
  "number_of_guests": 2,
  "user_email": "user@example.com",
  "user_phone": "+251911223344"
}
```

### 2. Initiate Payment
```python
# Initiate payment for the booking
POST /api/payments/initiate/
{
  "booking_id": 1,
  "return_url": "http://localhost:3000/payment/success"
}

# Response includes payment_url
# Redirect user to payment_url
```

### 3. User Completes Payment
- User is redirected to Chapa checkout page
- User enters payment details
- Chapa processes payment
- User is redirected to return_url

### 4. Verify Payment
```python
# Verify payment status
POST /api/payments/verify/
{
  "transaction_id": "TXN-..."
}

# If successful:
# - Payment status updated to "completed"
# - Booking status updated to "confirmed"
# - Confirmation email sent to user
```

### 5. Webhook (Automatic)
- Chapa sends webhook notification when payment completes
- System automatically updates payment and booking status
- Confirmation email sent if not already sent

## Testing

### Run Unit Tests
```bash
python manage.py test listings
```

### Test with Chapa Sandbox

1. **Use Test API Keys**
   - Set `CHAPA_SECRET_KEY` to your test key in `.env`

2. **Test Payment Flow**
   ```bash
   # Create a test booking via API or admin
   # Initiate payment
   # Use test card numbers from Chapa documentation
   ```

3. **Test Cards** (from Chapa docs)
   - Success: Use test cards provided by Chapa
   - Check Chapa documentation for test card numbers

### Manual Testing Checklist

- [ ] Create a listing
- [ ] Create a booking
- [ ] Initiate payment (check payment_url is generated)
- [ ] Complete payment in Chapa sandbox
- [ ] Verify payment status
- [ ] Check email notifications (console or SMTP)
- [ ] Verify webhook handling
- [ ] Check Django admin for payment records

## Payment Status Flow

```
pending → completed (successful payment)
pending → failed (payment failed)
pending → cancelled (payment cancelled by user)
```

## Email Notifications

### Payment Confirmation Email
Sent when payment is successfully verified:
- Booking reference
- Listing details
- Check-in/check-out dates
- Payment amount and ID

### Payment Failure Email
Sent when payment fails:
- Booking reference
- Failure reason
- Instructions to retry

### Celery Tasks
- `send_payment_confirmation_email`: Async task for success emails
- `send_payment_failed_email`: Async task for failure emails
- `check_pending_payments`: Periodic task to verify pending payments

## Error Handling

### Common Errors

1. **Payment Initiation Failed**
   - Check Chapa API key is correct
   - Verify internet connection
   - Check Chapa API status

2. **Payment Verification Failed**
   - Transaction may still be processing
   - Wait and retry verification
   - Check transaction ID is correct

3. **Webhook Not Received**
   - Ensure webhook URL is publicly accessible
   - Check webhook secret matches
   - Verify webhook URL in Chapa dashboard

## Security Best Practices

1. **API Keys**
   - Never commit `.env` file
   - Use environment variables
   - Rotate keys regularly

2. **Webhook Verification**
   - Verify webhook signatures (implement CHAPA_WEBHOOK_SECRET check)
   - Validate payload data
   - Log all webhook requests

3. **Payment Verification**
   - Always verify payments server-side
   - Never trust client-side payment status
   - Implement idempotency for payment processing

## Production Deployment

### Configuration Changes

1. **Settings**
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['yourdomain.com']
   CHAPA_SECRET_KEY = 'live-secret-key'
   ```

2. **Database**
   - Use PostgreSQL or MySQL
   - Configure DATABASE_URL

3. **Email**
   - Configure SMTP settings
   - Use production email service

4. **Static Files**
   ```bash
   python manage.py collectstatic
   ```

5. **Security**
   - Enable HTTPS
   - Configure CSRF settings
   - Set secure cookies

## Monitoring and Logging

### Payment Logs
- All payment operations are logged
- Check logs for payment initiation, verification, and webhook events

### Django Admin
- Monitor payments in Django admin
- View payment responses and verification data
- Track booking and payment status

## Troubleshooting

### Payment Stuck in Pending
- Run verification manually
- Check Chapa dashboard for transaction status
- Review webhook logs

### Emails Not Sending
- Check Celery worker is running
- Verify email configuration
- Check email backend (console vs SMTP)

### Webhook Not Working
- Ensure URL is publicly accessible
- Check webhook configuration in Chapa dashboard
- Review server logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is created for educational purposes as part of ALX Software Engineering program.

## Support

For issues related to:
- **Chapa API**: Contact Chapa support or check documentation at https://developer.chapa.co/
- **Project**: Open an issue in the repository

## Repository Information

- **GitHub Repository**: alx_travel_app_0x02
- **Directory**: alx_travel_app
- **Key Files**: 
  - `listings/views.py` - Payment API endpoints
  - `listings/models.py` - Payment model
  - `README.md` - This documentation

## Version History

- **v0x02**: Chapa payment integration
- Features: Payment initiation, verification, webhooks, email notifications
