from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta
from .models import Listing, Booking, Payment
from unittest.mock import patch, MagicMock


class PaymentIntegrationTestCase(APITestCase):
    """Test cases for Chapa payment integration."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test listing
        self.listing = Listing.objects.create(
            title='Test Villa',
            description='A beautiful test villa',
            location='Addis Ababa',
            price_per_night=Decimal('1000.00'),
            available=True
        )
        
        # Create test booking
        self.booking = Booking.objects.create(
            user=self.user,
            listing=self.listing,
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=10),
            number_of_guests=2,
            total_amount=Decimal('3000.00'),
            user_email='test@example.com',
            user_phone='+251911223344'
        )
        
        self.client.force_authenticate(user=self.user)
    
    @patch('listings.services.requests.post')
    def test_initiate_payment_success(self, mock_post):
        """Test successful payment initiation."""
        # Mock Chapa API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'message': 'Payment initiated',
            'data': {
                'checkout_url': 'https://checkout.chapa.co/test',
                'tx_ref': 'TXN-TEST-123'
            }
        }
        mock_post.return_value = mock_response
        
        url = reverse('initiate-payment')
        data = {
            'booking_id': self.booking.id,
            'return_url': 'http://localhost:3000/payment/success'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('payment_url', response.data)
        self.assertIn('payment_id', response.data)
        
        # Verify payment was created
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.amount, self.booking.total_amount)
    
    @patch('listings.services.requests.get')
    def test_verify_payment_success(self, mock_get):
        """Test successful payment verification."""
        # Create payment
        payment = Payment.objects.create(
            booking=self.booking,
            booking_reference=str(self.booking.booking_reference),
            transaction_id='TXN-TEST-123',
            amount=self.booking.total_amount,
            currency='ETB',
            status='pending',
            user_email=self.booking.user_email,
            user_phone=self.booking.user_phone
        )
        
        # Mock Chapa verification response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'message': 'Payment verified',
            'data': {
                'status': 'success',
                'amount': '3000.00',
                'currency': 'ETB'
            }
        }
        mock_get.return_value = mock_response
        
        url = reverse('verify-payment')
        data = {'transaction_id': payment.transaction_id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify payment status updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'completed')
        
        # Verify booking status updated
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')
    
    def test_initiate_payment_invalid_booking(self):
        """Test payment initiation with invalid booking ID."""
        url = reverse('initiate-payment')
        data = {
            'booking_id': 99999,
            'return_url': 'http://localhost:3000/payment/success'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_payment_already_completed(self):
        """Test that completed payments cannot be re-initiated."""
        # Create completed payment
        Payment.objects.create(
            booking=self.booking,
            booking_reference=str(self.booking.booking_reference),
            transaction_id='TXN-TEST-123',
            amount=self.booking.total_amount,
            currency='ETB',
            status='completed',
            user_email=self.booking.user_email,
            user_phone=self.booking.user_phone
        )
        
        url = reverse('initiate-payment')
        data = {
            'booking_id': self.booking.id,
            'return_url': 'http://localhost:3000/payment/success'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already been completed', response.data['error'])
