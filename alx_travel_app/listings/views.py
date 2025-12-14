from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging
import uuid

from .models import Listing, Booking, Payment
from .serializers import (
    ListingSerializer, BookingSerializer, BookingCreateSerializer,
    PaymentSerializer, PaymentInitiateSerializer, PaymentVerifySerializer
)
from .services import ChapaPaymentService
from .tasks import send_payment_confirmation_email, send_payment_failed_email

logger = logging.getLogger(__name__)


class ListingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing listings."""
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Allow anyone to view listings."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Check availability of a listing."""
        listing = self.get_object()
        return Response({
            'available': listing.available,
            'listing_id': listing.id,
            'title': listing.title,
            'price_per_night': listing.price_per_night
        })


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bookings."""
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        """Filter bookings by authenticated user."""
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)

    @action(detail=True, methods=['get'])
    def payment_status(self, request, pk=None):
        """Get payment status for a booking."""
        booking = self.get_object()
        
        if not hasattr(booking, 'payment'):
            return Response({
                'booking_reference': str(booking.booking_reference),
                'payment_exists': False,
                'message': 'No payment initiated for this booking'
            })
        
        payment = booking.payment
        return Response({
            'booking_reference': str(booking.booking_reference),
            'payment_exists': True,
            'payment_status': payment.status,
            'payment_id': str(payment.payment_id),
            'amount': payment.amount,
            'payment_url': payment.payment_url
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """
    Initiate a payment for a booking using Chapa API.
    
    Request Body:
        - booking_id: ID of the booking to pay for
        - return_url: URL to redirect user after payment
        - callback_url: (optional) URL for Chapa webhook notifications
    
    Returns:
        Payment details including payment URL
    """
    serializer = PaymentInitiateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    booking_id = serializer.validated_data['booking_id']
    return_url = serializer.validated_data['return_url']
    callback_url = serializer.validated_data.get('callback_url', '')
    
    try:
        with transaction.atomic():
            # Get booking
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Check if user owns this booking
            if booking.user != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'You do not have permission to pay for this booking.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if payment already exists
            if hasattr(booking, 'payment'):
                payment = booking.payment
                if payment.status == 'completed':
                    return Response(
                        {'error': 'Payment for this booking has already been completed.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif payment.status == 'pending':
                    return Response({
                        'message': 'Payment already initiated',
                        'payment_url': payment.payment_url,
                        'payment_id': str(payment.payment_id),
                        'status': payment.status
                    })
            
            # Generate unique transaction reference
            tx_ref = f"TXN-{booking.booking_reference}-{uuid.uuid4().hex[:8]}"
            
            # Get user details
            user = request.user
            first_name = user.first_name or 'Customer'
            last_name = user.last_name or 'User'
            
            # Initialize Chapa payment service
            chapa_service = ChapaPaymentService()
            
            # Prepare customization
            customization = {
                'title': 'ALX Travel App Booking Payment',
                'description': f'Payment for booking {booking.booking_reference}'
            }
            
            # Initiate payment with Chapa
            payment_result = chapa_service.initiate_payment(
                amount=float(booking.total_amount),
                currency='ETB',
                email=booking.user_email,
                first_name=first_name,
                last_name=last_name,
                phone_number=booking.user_phone,
                tx_ref=tx_ref,
                callback_url=callback_url or f"{request.build_absolute_uri('/api/payments/webhook/')}",
                return_url=return_url,
                customization=customization
            )
            
            if not payment_result['success']:
                logger.error(f"Payment initiation failed: {payment_result.get('error')}")
                return Response(
                    {'error': f"Payment initiation failed: {payment_result.get('error')}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Extract payment data
            payment_data = payment_result['data']
            checkout_url = payment_data.get('checkout_url')
            
            # Create or update payment record
            if hasattr(booking, 'payment'):
                payment = booking.payment
                payment.transaction_id = tx_ref
                payment.chapa_reference = payment_data.get('tx_ref')
                payment.payment_url = checkout_url
                payment.payment_response = payment_result
                payment.status = 'pending'
                payment.save()
            else:
                payment = Payment.objects.create(
                    booking=booking,
                    booking_reference=str(booking.booking_reference),
                    transaction_id=tx_ref,
                    chapa_reference=payment_data.get('tx_ref'),
                    amount=booking.total_amount,
                    currency='ETB',
                    payment_method='chapa',
                    status='pending',
                    payment_url=checkout_url,
                    payment_response=payment_result,
                    user_email=booking.user_email,
                    user_phone=booking.user_phone
                )
            
            logger.info(f"Payment initiated successfully for booking {booking.booking_reference}")
            
            return Response({
                'success': True,
                'message': 'Payment initiated successfully',
                'payment_id': str(payment.payment_id),
                'payment_url': checkout_url,
                'transaction_id': tx_ref,
                'amount': str(booking.total_amount),
                'currency': 'ETB',
                'status': 'pending'
            }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}", exc_info=True)
        return Response(
            {'error': f'An error occurred: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """
    Verify a payment with Chapa and update payment status.
    
    Request Body:
        - transaction_id: Transaction ID to verify
    
    Returns:
        Updated payment status
    """
    serializer = PaymentVerifySerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    transaction_id = serializer.validated_data['transaction_id']
    
    try:
        # Get payment record
        payment = get_object_or_404(Payment, transaction_id=transaction_id)
        
        # Check permission
        if payment.booking.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to verify this payment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If already completed, return current status
        if payment.status == 'completed':
            return Response({
                'message': 'Payment already verified and completed',
                'status': payment.status,
                'payment_id': str(payment.payment_id),
                'amount': str(payment.amount),
                'completed_at': payment.completed_at
            })
        
        # Verify with Chapa
        chapa_service = ChapaPaymentService()
        verification_result = chapa_service.verify_payment(transaction_id)
        
        # Store verification response
        payment.verification_response = verification_result
        
        if not verification_result['success']:
            payment.mark_as_failed(error_message=verification_result.get('error'))
            
            # Send failure email asynchronously
            send_payment_failed_email.delay(
                payment_id=payment.id,
                reason=verification_result.get('error', 'Verification failed')
            )
            
            return Response({
                'success': False,
                'message': 'Payment verification failed',
                'error': verification_result.get('error'),
                'status': payment.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check payment status from Chapa
        verification_data = verification_result['data']
        chapa_status = verification_data.get('status', '').lower()
        
        if chapa_status == 'success':
            # Mark payment as completed
            payment.mark_as_completed()
            
            # Update booking status
            booking = payment.booking
            booking.status = 'confirmed'
            booking.save()
            
            # Send confirmation email asynchronously
            send_payment_confirmation_email.delay(
                payment_id=payment.id,
                booking_id=booking.id
            )
            
            logger.info(f"Payment verified and completed for transaction {transaction_id}")
            
            return Response({
                'success': True,
                'message': 'Payment verified successfully',
                'payment_id': str(payment.payment_id),
                'status': payment.status,
                'amount': str(payment.amount),
                'booking_reference': str(booking.booking_reference),
                'booking_status': booking.status,
                'completed_at': payment.completed_at
            })
        else:
            # Payment not successful
            payment.mark_as_failed(error_message=f"Chapa status: {chapa_status}")
            
            # Send failure email
            send_payment_failed_email.delay(
                payment_id=payment.id,
                reason=f"Payment status: {chapa_status}"
            )
            
            return Response({
                'success': False,
                'message': f'Payment not successful. Status: {chapa_status}',
                'status': payment.status,
                'chapa_status': chapa_status
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}", exc_info=True)
        return Response(
            {'error': f'An error occurred: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def chapa_webhook(request):
    """
    Handle webhook notifications from Chapa.
    This endpoint receives payment status updates from Chapa.
    """
    try:
        # Log webhook data
        logger.info(f"Received Chapa webhook: {request.data}")
        
        # Extract transaction reference
        tx_ref = request.data.get('tx_ref') or request.data.get('trx_ref')
        
        if not tx_ref:
            logger.error("Webhook missing transaction reference")
            return Response(
                {'error': 'Missing transaction reference'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find payment by transaction ID
        try:
            payment = Payment.objects.get(transaction_id=tx_ref)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for tx_ref: {tx_ref}")
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get status from webhook
        webhook_status = request.data.get('status', '').lower()
        
        # Update payment based on webhook status
        if webhook_status == 'success':
            if payment.status != 'completed':
                payment.mark_as_completed()
                
                # Update booking
                booking = payment.booking
                booking.status = 'confirmed'
                booking.save()
                
                # Send confirmation email
                send_payment_confirmation_email.delay(
                    payment_id=payment.id,
                    booking_id=booking.id
                )
                
                logger.info(f"Payment completed via webhook for {tx_ref}")
        elif webhook_status in ['failed', 'cancelled']:
            payment.mark_as_failed(error_message=f"Webhook status: {webhook_status}")
            
            # Send failure email
            send_payment_failed_email.delay(
                payment_id=payment.id,
                reason=f"Payment {webhook_status}"
            )
            
            logger.info(f"Payment failed via webhook for {tx_ref}")
        
        # Store webhook data
        payment.verification_response = request.data
        payment.save()
        
        return Response({'success': True}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_detail(request, payment_id):
    """Get details of a specific payment."""
    try:
        payment = get_object_or_404(Payment, payment_id=payment_id)
        
        # Check permission
        if payment.booking.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to view this payment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error retrieving payment: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_payments(request):
    """Get all payments for the authenticated user."""
    try:
        bookings = Booking.objects.filter(user=request.user)
        payments = Payment.objects.filter(booking__in=bookings).order_by('-created_at')
        
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error retrieving user payments: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
