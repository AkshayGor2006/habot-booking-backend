import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class PaymentGatewayError(Exception):
    """Raised when the payment gateway cannot be reached or fails."""


def initiate_payment(booking_id, amount):
    url = f"{settings.PAYMENT_GATEWAY_URL}/charge/"

    payload = {
        "booking_id": booking_id,
        "amount": amount,
        "currency": "INR",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=5,
        )

        response.raise_for_status()

        return response.json()

    except requests.Timeout:
        logger.exception(
            "Payment gateway timed out for booking %s",
            booking_id,
        )
        raise PaymentGatewayError(
            "Payment gateway timed out."
        )

    except requests.RequestException:
        logger.exception(
            "Payment gateway request failed for booking %s",
            booking_id,
        )
        raise PaymentGatewayError(
            "Payment gateway request failed."
        )