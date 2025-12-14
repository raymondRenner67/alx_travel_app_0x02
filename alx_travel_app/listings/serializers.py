from rest_framework import serializers
from .models import Listing, Booking, Payment
from django.contrib.auth.models import User


class ListingSerializer(serializers.ModelSerializer):
    """Serializer for Listing model."""
    class Meta:
        model = Listing
        fields = ['id', 'title', 'description', 'location', 'price_per_night', 'available', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model."""
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'user', 'username', 'listing', 'listing_title',
            'check_in_date', 'check_out_date', 'number_of_guests', 'total_amount',
            'status', 'user_email', 'user_phone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'booking_reference', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate booking dates."""
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')

        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError({
                    'check_out_date': 'Check-out date must be after check-in date.'
                })

        return data


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings."""
    class Meta:
        model = Booking
        fields = [
            'listing', 'check_in_date', 'check_out_date', 'number_of_guests',
            'user_email', 'user_phone'
        ]

    def validate(self, data):
        """Validate booking dates."""
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')

        if check_out <= check_in:
            raise serializers.ValidationError({
                'check_out_date': 'Check-out date must be after check-in date.'
            })

        # Check if listing is available
        listing = data.get('listing')
        if not listing.available:
            raise serializers.ValidationError({
                'listing': 'This listing is not available for booking.'
            })

        return data

    def create(self, validated_data):
        """Create booking with calculated total amount."""
        listing = validated_data['listing']
        check_in = validated_data['check_in_date']
        check_out = validated_data['check_out_date']
        
        # Calculate total amount
        days = (check_out - check_in).days
        total_amount = listing.price_per_night * days
        
        validated_data['total_amount'] = total_amount
        validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    booking_details = BookingSerializer(source='booking', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'payment_id', 'booking', 'booking_details', 'booking_reference',
            'transaction_id', 'chapa_reference', 'amount', 'currency',
            'payment_method', 'status', 'payment_url', 'user_email', 'user_phone',
            'error_message', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'payment_id', 'transaction_id', 'chapa_reference', 'payment_url',
            'created_at', 'updated_at', 'completed_at'
        ]


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for initiating payment."""
    booking_id = serializers.IntegerField()
    return_url = serializers.URLField()
    callback_url = serializers.URLField(required=False, allow_blank=True)

    def validate_booking_id(self, value):
        """Validate that booking exists and belongs to user."""
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

        # Check if payment already exists
        if hasattr(booking, 'payment'):
            if booking.payment.status in ['completed', 'pending']:
                raise serializers.ValidationError(
                    f"Payment for this booking already exists with status: {booking.payment.status}"
                )

        return value


class PaymentVerifySerializer(serializers.Serializer):
    """Serializer for verifying payment."""
    transaction_id = serializers.CharField(max_length=255)
