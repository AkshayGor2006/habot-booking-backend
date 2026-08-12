"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from bookings.views import (
    BookingCreateView,
    LSASearchView,
    mock_payment_charge,
    payment_webhook,
)

urlpatterns = [
    path("admin/", admin.site.urls),

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
        "api/v1/mock-payment/charge/",
        mock_payment_charge,
        name="mock-payment-charge",
    ),

    path(
        "api/v1/payments/webhook/",
        payment_webhook,
        name="payment-webhook",
    ),
]