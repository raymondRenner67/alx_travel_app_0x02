# Quick Reference Card - ALX Travel App Payment Integration

## 🚀 Quick Start (3 Steps)

```bash
# 1. Install & Configure
cd alx_travel_app
pip install -r requirements.txt
cp .env.example .env
# Edit .env: Add CHAPA_SECRET_KEY

# 2. Initialize Database
python manage.py migrate
python manage.py createsuperuser

# 3. Run Application (3 terminals)
python manage.py runserver              # Terminal 1
redis-server                            # Terminal 2
celery -A alx_travel_app worker -l info # Terminal 3
```

## 📌 Important URLs

- **Admin Panel:** http://localhost:8000/admin
- **API Root:** http://localhost:8000/api/
- **Listings:** http://localhost:8000/api/listings/
- **Bookings:** http://localhost:8000/api/bookings/
- **Payments:** http://localhost:8000/api/payments/

## 🔑 API Endpoints Quick Reference

### Initiate Payment
```bash
POST /api/payments/initiate/
{
  "booking_id": 1,
  "return_url": "http://yoursite.com/success"
}
```

### Verify Payment
```bash
POST /api/payments/verify/
{
  "transaction_id": "TXN-xxx"
}
```

### Get Payment Details
```bash
GET /api/payments/{payment_id}/
```

### Webhook
```bash
POST /api/payments/webhook/
# Chapa sends this automatically
```

## 🔧 Configuration Files

- **Settings:** `alx_travel_app/settings.py`
- **Environment:** `.env`
- **URLs:** `listings/urls.py`
- **Models:** `listings/models.py`
- **Views:** `listings/views.py`
- **Services:** `listings/services.py`
- **Tasks:** `listings/tasks.py`

## 📊 Models

### Payment Model Fields
- `payment_id` - UUID (Primary Key)
- `booking` - ForeignKey to Booking
- `transaction_id` - Chapa transaction reference
- `amount` - Payment amount (Decimal)
- `status` - pending/completed/failed
- `payment_url` - Chapa checkout URL
- `payment_response` - JSON response from Chapa
- `verification_response` - JSON verification data

## 🔄 Payment Workflow

1. **Create Booking** → Booking ID generated
2. **Initiate Payment** → Get Chapa checkout URL
3. **User Pays** → Redirect to Chapa
4. **Webhook** → Auto-update status (or manual verify)
5. **Confirmed** → Email sent, booking confirmed

## ⚙️ Environment Variables

```env
# Required
CHAPA_SECRET_KEY=CHASECK-your-key
DJANGO_SECRET_KEY=your-secret

# Optional
DEBUG=True
CELERY_BROKER_URL=redis://localhost:6379/0
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## 🧪 Testing

```bash
# Run tests
python manage.py test listings

# Demo script
python demo_payment.py

# Verify installation
python verify_installation.py
```

## 📁 Key Files

| File | Description |
|------|-------------|
| `listings/models.py` | Payment, Booking, Listing models |
| `listings/views.py` | Payment API endpoints |
| `listings/services.py` | Chapa API integration |
| `listings/tasks.py` | Email notification tasks |
| `README.md` | Complete documentation |
| `SETUP.md` | Quick setup guide |
| `API_TESTING.md` | API examples |
| `DEPLOYMENT.md` | Production guide |

## 🐛 Troubleshooting

### "CHAPA_SECRET_KEY not found"
```bash
cp .env.example .env
# Edit .env and add your key
```

### "Redis connection failed"
```bash
redis-server
```

### "Migration errors"
```bash
python manage.py makemigrations
python manage.py migrate
```

### "Payment verification failed"
- Check Chapa API key is valid
- Ensure internet connection
- Wait 1-2 minutes for processing

## 📞 Get Help

- **Chapa Docs:** https://developer.chapa.co/
- **Dashboard:** https://dashboard.chapa.co/
- **Full Docs:** See `README.md` in alx_travel_app/
- **Setup Guide:** See `SETUP.md`
- **Testing Log:** See `TESTING_LOG.md`

## ✅ Checklist

- [ ] Dependencies installed
- [ ] .env configured with CHAPA_SECRET_KEY
- [ ] Database migrated
- [ ] Superuser created
- [ ] Redis running
- [ ] Celery worker running
- [ ] Django server running
- [ ] Test payment completed

## 🎯 Common Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver

# Run Celery
celery -A alx_travel_app worker -l info

# Run tests
python manage.py test

# Collect static
python manage.py collectstatic

# Shell
python manage.py shell
```

## 📈 Status Codes

- **200** - Success
- **201** - Created (payment initiated)
- **400** - Bad Request (validation error)
- **403** - Forbidden (permission denied)
- **404** - Not Found
- **500** - Server Error

## 🔐 Security Notes

- Never commit `.env` file
- Use test keys for development
- Use live keys for production
- Verify payments server-side
- Enable HTTPS in production

---

**Quick Start Time:** ~5 minutes  
**Documentation:** Complete  
**Status:** ✅ Production Ready

For detailed information, see the full documentation in the `alx_travel_app/` directory.
