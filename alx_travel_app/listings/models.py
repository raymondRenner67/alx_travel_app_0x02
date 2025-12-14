from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Listing(models.Model):
    """Model representing a travel listing/property."""
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class Booking(models.Model):
    """Model representing a booking made by a user."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    booking_reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user_email = models.EmailField()
    user_phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']

    def calculate_total(self):
        """Calculate total amount based on listing price and duration."""
        days = (self.check_out_date - self.check_in_date).days
        return self.listing.price_per_night * days


class Payment(models.Model):
    """Model to store payment-related information for bookings."""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('chapa', 'Chapa'),
        ('manual', 'Manual'),
    ]

    payment_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    booking_reference = models.CharField(max_length=255, db_index=True)
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    chapa_reference = models.CharField(max_length=255, unique=True, null=True, blank=True)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='ETB')
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='chapa'
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_url = models.URLField(max_length=500, null=True, blank=True)
    payment_response = models.JSONField(null=True, blank=True)
    verification_response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    user_email = models.EmailField()
    user_phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.payment_id} - {self.status}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['chapa_reference']),
            models.Index(fields=['status']),
        ]

    def mark_as_completed(self):
        """Mark payment as completed and update timestamp."""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def mark_as_failed(self, error_message=None):
        """Mark payment as failed with optional error message."""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()
