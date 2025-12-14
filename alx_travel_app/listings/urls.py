from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'listings', views.ListingViewSet, basename='listing')
router.register(r'bookings', views.BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
    path('payments/initiate/', views.initiate_payment, name='initiate-payment'),
    path('payments/verify/', views.verify_payment, name='verify-payment'),
    path('payments/webhook/', views.chapa_webhook, name='chapa-webhook'),
    path('payments/<uuid:payment_id>/', views.payment_detail, name='payment-detail'),
    path('payments/', views.user_payments, name='user-payments'),
]
