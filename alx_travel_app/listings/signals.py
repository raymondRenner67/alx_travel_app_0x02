from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment, Booking
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def payment_status_changed(sender, instance, created, **kwargs):
    """
    Signal handler for payment status changes.
    """
    if not created and instance.status == 'completed':
        logger.info(f"Payment {instance.payment_id} completed for booking {instance.booking.booking_reference}")
