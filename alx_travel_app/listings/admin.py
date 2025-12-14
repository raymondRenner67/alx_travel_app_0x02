from django.contrib import admin
from .models import Listing, Booking, Payment


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'location', 'price_per_night', 'available', 'created_at']
    list_filter = ['available', 'created_at']
    search_fields = ['title', 'location', 'description']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'user', 'listing', 'check_in_date', 'check_out_date', 'status', 'total_amount']
    list_filter = ['status', 'created_at']
    search_fields = ['booking_reference', 'user__username', 'user_email']
    readonly_fields = ['booking_reference', 'created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'booking_reference', 'transaction_id', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['payment_id', 'transaction_id', 'chapa_reference', 'booking_reference', 'user_email']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'completed_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'booking', 'booking_reference', 'amount', 'currency', 'payment_method')
        }),
        ('Chapa Details', {
            'fields': ('transaction_id', 'chapa_reference', 'payment_url')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('User Information', {
            'fields': ('user_email', 'user_phone')
        }),
        ('API Responses', {
            'fields': ('payment_response', 'verification_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
