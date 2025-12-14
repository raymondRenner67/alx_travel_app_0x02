# Quick Setup Guide for ALX Travel App

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
cd alx_travel_app
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and add your Chapa API key:
```
CHAPA_SECRET_KEY=CHASECK-your-key-here
```

### 3. Initialize Database
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Start Services

**Terminal 1 - Django Server:**
```bash
python manage.py runserver
```

**Terminal 2 - Redis:**
```bash
redis-server
```

**Terminal 3 - Celery Worker:**
```bash
celery -A alx_travel_app worker -l info
```

### 5. Access the Application
- Admin: http://localhost:8000/admin
- API: http://localhost:8000/api/

## Testing Payment Integration

### Step-by-Step Test

1. **Create a Listing** (via admin or API)
   ```bash
   # Login to admin panel
   # Create a listing with price_per_night = 1000
   ```

2. **Create a Booking** (via API)
   ```bash
   POST http://localhost:8000/api/bookings/
   {
     "listing": 1,
     "check_in_date": "2025-12-20",
     "check_out_date": "2025-12-23",
     "number_of_guests": 2,
     "user_email": "test@example.com",
     "user_phone": "+251911223344"
   }
   ```

3. **Initiate Payment**
   ```bash
   POST http://localhost:8000/api/payments/initiate/
   {
     "booking_id": 1,
     "return_url": "http://localhost:3000/success"
   }
   ```

4. **Copy the payment_url from response and open in browser**

5. **Complete payment in Chapa sandbox**

6. **Verify Payment**
   ```bash
   POST http://localhost:8000/api/payments/verify/
   {
     "transaction_id": "TXN-..." # from initiate response
   }
   ```

## Expected Results

✅ Payment initiated successfully
✅ Payment URL generated
✅ Payment verification successful
✅ Booking status updated to "confirmed"
✅ Payment status updated to "completed"
✅ Confirmation email sent (check console or inbox)

## Common Issues

### "CHAPA_SECRET_KEY not found"
- Make sure `.env` file exists
- Check CHAPA_SECRET_KEY is set correctly

### "Redis connection error"
- Start Redis server: `redis-server`

### "Emails not sending"
- Start Celery worker
- Check EMAIL_BACKEND in settings

### "Payment verification failed"
- Check internet connection
- Verify Chapa API key is valid
- Transaction might still be processing (wait 1-2 minutes)

## Next Steps

1. Review the API documentation in README.md
2. Test webhook integration
3. Configure production email settings
4. Deploy to production environment

## Support

Check the main README.md for detailed documentation.
