from django.urls import path

from .views import BookingCreateView, LSASearchView, mock_payment_charge, payment_webhook


urlpatterns = [
    path(
        "api/v1/bookings/",
        BookingCreateView.as_view(),
        name="booking-create",
    ),
    path(
        "api/v1/lsas/search/",
        LSASearchView.as_view(),
        name="lsa-search",
    ),
    path(
        "api/mock-payment/charge/",
         mock_payment_charge,
        name="mock-payment-charge",
    ),
    path(
        "api/v1/payments/webhook/",
        payment_webhook,
        name="payment-webhook",
    ),
]