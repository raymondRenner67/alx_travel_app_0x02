# Production Deployment Guide

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Python 3.8+
- PostgreSQL 12+
- Nginx
- Redis
- Domain name with SSL certificate

## 1. Server Setup

### Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### Install Dependencies
```bash
sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx redis-server -y
```

## 2. Database Setup

### Create PostgreSQL Database
```bash
sudo -u postgres psql

CREATE DATABASE alx_travel_app;
CREATE USER alx_user WITH PASSWORD 'secure_password_here';
ALTER ROLE alx_user SET client_encoding TO 'utf8';
ALTER ROLE alx_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE alx_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE alx_travel_app TO alx_user;
\q
```

## 3. Application Setup

### Clone Repository
```bash
cd /var/www
sudo git clone <your-repo-url> alx_travel_app
cd alx_travel_app/alx_travel_app
sudo chown -R $USER:$USER /var/www/alx_travel_app
```

### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Configure Environment Variables
```bash
nano .env
```

Add production settings:
```env
DJANGO_SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://alx_user:secure_password_here@localhost:5432/alx_travel_app

# Chapa API (LIVE KEYS)
CHAPA_SECRET_KEY=CHASECK-your-live-key-here
CHAPA_WEBHOOK_SECRET=your-webhook-secret

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email (Production SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Update settings.py for Production
```python
# In settings.py, add:
import dj_database_url

# Database configuration
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
    )
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py createsuperuser
```

## 4. Gunicorn Setup

### Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add:
```ini
[Unit]
Description=Gunicorn daemon for ALX Travel App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/alx_travel_app/alx_travel_app
Environment="PATH=/var/www/alx_travel_app/alx_travel_app/venv/bin"
ExecStart=/var/www/alx_travel_app/alx_travel_app/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/alx_travel_app/alx_travel_app/gunicorn.sock \
          alx_travel_app.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Start Gunicorn
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

## 5. Celery Setup

### Create Celery Worker Service
```bash
sudo nano /etc/systemd/system/celery.service
```

Add:
```ini
[Unit]
Description=Celery Worker for ALX Travel App
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/alx_travel_app/alx_travel_app
Environment="PATH=/var/www/alx_travel_app/alx_travel_app/venv/bin"
ExecStart=/var/www/alx_travel_app/alx_travel_app/venv/bin/celery -A alx_travel_app worker -l info

[Install]
WantedBy=multi-user.target
```

### Start Celery
```bash
sudo systemctl start celery
sudo systemctl enable celery
sudo systemctl status celery
```

## 6. Nginx Configuration

### Create Nginx Config
```bash
sudo nano /etc/nginx/sites-available/alx_travel_app
```

Add:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/alx_travel_app/alx_travel_app;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/alx_travel_app/alx_travel_app/gunicorn.sock;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/alx_travel_app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. SSL Certificate (Let's Encrypt)

### Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Obtain Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 8. Chapa Webhook Configuration

### Configure Webhook URL in Chapa Dashboard
1. Go to https://dashboard.chapa.co/
2. Navigate to Settings > Webhooks
3. Add webhook URL: `https://yourdomain.com/api/payments/webhook/`
4. Save webhook secret to `.env`

### Test Webhook
```bash
# Send test webhook from Chapa dashboard
# Check logs: sudo journalctl -u gunicorn -f
```

## 9. Monitoring and Logging

### Setup Log Directory
```bash
sudo mkdir -p /var/log/alx_travel_app
sudo chown www-data:www-data /var/log/alx_travel_app
```

### Configure Django Logging
Add to `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/alx_travel_app/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### View Logs
```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Celery logs
sudo journalctl -u celery -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs
sudo tail -f /var/log/alx_travel_app/django.log
```

## 10. Backup Strategy

### Database Backup Script
```bash
#!/bin/bash
# /var/www/alx_travel_app/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/alx_travel_app"
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U alx_user alx_travel_app > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/alx_travel_app/alx_travel_app/media/

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete
```

### Setup Cron Job
```bash
crontab -e

# Add daily backup at 2 AM
0 2 * * * /var/www/alx_travel_app/backup.sh
```

## 11. Security Checklist

- [ ] DEBUG = False
- [ ] Strong SECRET_KEY
- [ ] HTTPS enabled
- [ ] Secure cookies enabled
- [ ] PostgreSQL user has limited privileges
- [ ] Firewall configured (allow only 80, 443, 22)
- [ ] SSH key-based authentication
- [ ] Regular security updates
- [ ] Chapa live keys secured
- [ ] Environment variables not in version control

## 12. Performance Optimization

### Enable Gzip Compression
Add to Nginx config:
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

### Configure Caching
```python
# In settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 13. Deployment Checklist

- [ ] Server configured and secured
- [ ] PostgreSQL database created
- [ ] Application code deployed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Environment variables configured
- [ ] Migrations applied
- [ ] Static files collected
- [ ] Gunicorn service running
- [ ] Celery service running
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Chapa webhook configured
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Testing completed

## 14. Testing in Production

### Test Payment Flow
1. Create test booking
2. Initiate payment with live Chapa keys
3. Complete payment (small amount)
4. Verify payment
5. Check email notifications
6. Verify webhook handling

### Monitor Logs
```bash
# Watch all services
sudo journalctl -u gunicorn -u celery -u nginx -f
```

## 15. Maintenance

### Update Application
```bash
cd /var/www/alx_travel_app
git pull origin main
source alx_travel_app/venv/bin/activate
pip install -r alx_travel_app/requirements.txt
python alx_travel_app/manage.py migrate
python alx_travel_app/manage.py collectstatic --no-input
sudo systemctl restart gunicorn celery
```

### Restart Services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart nginx
```

## Troubleshooting

### Gunicorn Won't Start
- Check socket file permissions
- Review systemd logs
- Verify Python path

### Payments Failing
- Check Chapa API keys (live vs test)
- Verify internet connectivity
- Review payment logs

### Emails Not Sending
- Check Celery worker status
- Verify SMTP credentials
- Review email logs

## Support

For production issues:
- Check application logs
- Review Chapa dashboard
- Contact Chapa support for payment issues
