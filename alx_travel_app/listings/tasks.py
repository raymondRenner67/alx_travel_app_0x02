from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_payment_confirmation_email(self, payment_id, booking_id):
    """
    Send payment confirmation email to user.
    
    Args:
        payment_id: ID of the payment
        booking_id: ID of the booking
    """
    try:
        from .models import Payment, Booking
        
        payment = Payment.objects.get(id=payment_id)
        booking = Booking.objects.get(id=booking_id)
        
        subject = f'Payment Confirmation - Booking {booking.booking_reference}'
        
        # Create email content
        context = {
            'booking_reference': booking.booking_reference,
            'listing_title': booking.listing.title,
            'check_in_date': booking.check_in_date,
            'check_out_date': booking.check_out_date,
            'number_of_guests': booking.number_of_guests,
            'total_amount': booking.total_amount,
            'payment_id': payment.payment_id,
            'transaction_id': payment.transaction_id,
            'payment_date': payment.completed_at,
        }
        
        # For now, using a simple text email
        # In production, you would use HTML templates
        message = f"""
        Dear Customer,

        Thank you for your payment!

        Your booking has been confirmed. Here are your booking details:

        Booking Reference: {booking.booking_reference}
        Listing: {booking.listing.title}
        Check-in Date: {booking.check_in_date}
        Check-out Date: {booking.check_out_date}
        Number of Guests: {booking.number_of_guests}
        Total Amount Paid: ETB {booking.total_amount}

        Payment Details:
        Payment ID: {payment.payment_id}
        Transaction ID: {payment.transaction_id}
        Payment Date: {payment.completed_at}

        We look forward to hosting you!

        Best regards,
        ALX Travel App Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.user_email],
            fail_silently=False,
        )
        
        logger.info(f"Payment confirmation email sent to {payment.user_email}")
        return f"Email sent successfully to {payment.user_email}"
    
    except Exception as e:
        logger.error(f"Error sending payment confirmation email: {str(e)}")
        # Retry the task
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_payment_failed_email(self, payment_id, reason):
    """
    Send payment failure notification email to user.
    
    Args:
        payment_id: ID of the payment
        reason: Reason for payment failure
    """
    try:
        from .models import Payment
        
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        
        subject = f'Payment Failed - Booking {booking.booking_reference}'
        
        message = f"""
        Dear Customer,

        We're sorry, but your payment for the following booking could not be processed:

        Booking Reference: {booking.booking_reference}
        Listing: {booking.listing.title}
        Amount: ETB {booking.total_amount}

        Reason: {reason}

        Please try again or contact our support team if the problem persists.

        Best regards,
        ALX Travel App Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.user_email],
            fail_silently=False,
        )
        
        logger.info(f"Payment failure email sent to {payment.user_email}")
        return f"Failure email sent successfully to {payment.user_email}"
    
    except Exception as e:
        logger.error(f"Error sending payment failure email: {str(e)}")
        # Retry the task
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def check_pending_payments():
    """
    Periodic task to check status of pending payments.
    This can be scheduled to run periodically using Celery Beat.
    """
    from .models import Payment
    from .services import ChapaPaymentService
    from django.utils import timezone
    from datetime import timedelta
    
    # Get payments that are pending for more than 10 minutes
    ten_minutes_ago = timezone.now() - timedelta(minutes=10)
    pending_payments = Payment.objects.filter(
        status='pending',
        created_at__lt=ten_minutes_ago
    )
    
    chapa_service = ChapaPaymentService()
    
    for payment in pending_payments:
        try:
            verification_result = chapa_service.verify_payment(payment.transaction_id)
            
            if verification_result['success']:
                verification_data = verification_result['data']
                chapa_status = verification_data.get('status', '').lower()
                
                if chapa_status == 'success':
                    payment.mark_as_completed()
                    
                    booking = payment.booking
                    booking.status = 'confirmed'
                    booking.save()
                    
                    send_payment_confirmation_email.delay(
                        payment_id=payment.id,
                        booking_id=booking.id
                    )
                    
                    logger.info(f"Auto-verified payment {payment.transaction_id}")
        
        except Exception as e:
            logger.error(f"Error checking payment {payment.transaction_id}: {str(e)}")
            continue
    
    return f"Checked {pending_payments.count()} pending payments"
