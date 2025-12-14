"""
Sample script demonstrating Chapa payment integration.
This script shows how to use the payment service programmatically.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')
django.setup()

from listings.models import Listing, Booking, Payment
from listings.services import ChapaPaymentService
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal


def create_sample_data():
    """Create sample listing and booking for testing."""
    print("=" * 50)
    print("Creating Sample Data")
    print("=" * 50)
    
    # Create or get user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Created user: {user.username}")
    else:
        print(f"✓ Using existing user: {user.username}")
    
    # Create listing
    listing, created = Listing.objects.get_or_create(
        title='Luxury Villa in Addis Ababa',
        defaults={
            'description': 'A beautiful luxury villa with amazing views',
            'location': 'Addis Ababa, Ethiopia',
            'price_per_night': Decimal('1500.00'),
            'available': True
        }
    )
    if created:
        print(f"✓ Created listing: {listing.title}")
    else:
        print(f"✓ Using existing listing: {listing.title}")
    
    # Create booking
    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=3)
    
    booking = Booking.objects.create(
        user=user,
        listing=listing,
        check_in_date=check_in,
        check_out_date=check_out,
        number_of_guests=2,
        total_amount=Decimal('4500.00'),
        user_email='test@example.com',
        user_phone='+251911223344'
    )
    print(f"✓ Created booking: {booking.booking_reference}")
    print(f"  Amount: ETB {booking.total_amount}")
    
    return user, listing, booking


def demonstrate_payment_initiation(booking):
    """Demonstrate payment initiation."""
    print("\n" + "=" * 50)
    print("Payment Initiation Demo")
    print("=" * 50)
    
    chapa_service = ChapaPaymentService()
    
    # Generate transaction reference
    import uuid
    tx_ref = f"TXN-{booking.booking_reference}-{uuid.uuid4().hex[:8]}"
    
    print(f"Transaction Reference: {tx_ref}")
    print("Initiating payment with Chapa...")
    
    # In a real scenario, you would call the actual API
    # For demo purposes, we'll simulate the response
    print("\n⚠️  NOTE: This is a demonstration.")
    print("In production, this would call the actual Chapa API.")
    
    # Simulated response
    simulated_response = {
        'success': True,
        'data': {
            'checkout_url': f'https://checkout.chapa.co/checkout/payment/{tx_ref}',
            'tx_ref': tx_ref
        },
        'message': 'Payment initiated successfully'
    }
    
    print("\nSimulated Chapa Response:")
    print(f"✓ Success: {simulated_response['success']}")
    print(f"✓ Checkout URL: {simulated_response['data']['checkout_url']}")
    print(f"✓ Transaction Reference: {simulated_response['data']['tx_ref']}")
    
    # Create payment record
    payment = Payment.objects.create(
        booking=booking,
        booking_reference=str(booking.booking_reference),
        transaction_id=tx_ref,
        chapa_reference=simulated_response['data']['tx_ref'],
        amount=booking.total_amount,
        currency='ETB',
        payment_method='chapa',
        status='pending',
        payment_url=simulated_response['data']['checkout_url'],
        payment_response=simulated_response,
        user_email=booking.user_email,
        user_phone=booking.user_phone
    )
    
    print(f"\n✓ Payment record created: {payment.payment_id}")
    print(f"  Status: {payment.status}")
    
    return payment


def demonstrate_payment_verification(payment):
    """Demonstrate payment verification."""
    print("\n" + "=" * 50)
    print("Payment Verification Demo")
    print("=" * 50)
    
    chapa_service = ChapaPaymentService()
    
    print(f"Transaction ID: {payment.transaction_id}")
    print("Verifying payment with Chapa...")
    
    # Simulated verification response
    simulated_verification = {
        'success': True,
        'data': {
            'status': 'success',
            'amount': str(payment.amount),
            'currency': payment.currency,
            'tx_ref': payment.transaction_id
        },
        'message': 'Payment verified successfully'
    }
    
    print("\nSimulated Verification Response:")
    print(f"✓ Success: {simulated_verification['success']}")
    print(f"✓ Status: {simulated_verification['data']['status']}")
    print(f"✓ Amount: ETB {simulated_verification['data']['amount']}")
    
    # Update payment status
    payment.mark_as_completed()
    payment.verification_response = simulated_verification
    payment.save()
    
    # Update booking status
    booking = payment.booking
    booking.status = 'confirmed'
    booking.save()
    
    print(f"\n✓ Payment status updated: {payment.status}")
    print(f"✓ Booking status updated: {booking.status}")
    print(f"✓ Completed at: {payment.completed_at}")


def demonstrate_webhook_handling():
    """Demonstrate webhook handling."""
    print("\n" + "=" * 50)
    print("Webhook Handling Demo")
    print("=" * 50)
    
    print("\nWebhook endpoint: /api/payments/webhook/")
    print("\nSample webhook payload from Chapa:")
    
    webhook_payload = {
        'tx_ref': 'TXN-abc123-def456',
        'status': 'success',
        'amount': '4500.00',
        'currency': 'ETB',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'charge': '67.50'
    }
    
    import json
    print(json.dumps(webhook_payload, indent=2))
    
    print("\n✓ Webhook received")
    print("✓ Payment status updated automatically")
    print("✓ Confirmation email sent")


def main():
    """Run the complete demonstration."""
    print("\n" + "=" * 50)
    print("CHAPA PAYMENT INTEGRATION DEMONSTRATION")
    print("ALX Travel App")
    print("=" * 50)
    
    # Step 1: Create sample data
    user, listing, booking = create_sample_data()
    
    # Step 2: Demonstrate payment initiation
    payment = demonstrate_payment_initiation(booking)
    
    # Step 3: Demonstrate payment verification
    demonstrate_payment_verification(payment)
    
    # Step 4: Demonstrate webhook handling
    demonstrate_webhook_handling()
    
    print("\n" + "=" * 50)
    print("DEMONSTRATION COMPLETE")
    print("=" * 50)
    print("\nSummary:")
    print(f"✓ Booking Reference: {booking.booking_reference}")
    print(f"✓ Payment ID: {payment.payment_id}")
    print(f"✓ Transaction ID: {payment.transaction_id}")
    print(f"✓ Amount: ETB {payment.amount}")
    print(f"✓ Payment Status: {payment.status}")
    print(f"✓ Booking Status: {booking.status}")
    
    print("\nTo test with actual Chapa API:")
    print("1. Add your CHAPA_SECRET_KEY to .env")
    print("2. Use the API endpoints: /api/payments/initiate/")
    print("3. Complete payment on Chapa checkout page")
    print("4. Verify payment: /api/payments/verify/")
    
    print("\n" + "=" * 50)


if __name__ == '__main__':
    main()
