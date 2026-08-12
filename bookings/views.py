import logging

from django.db.models import Exists, OuterRef
from django.utils.dateparse import parse_datetime

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .lsa_serializers import LSASearchSerializer
from .models import BookingRequest, LSAProfile
from .serializers import BookingRequestSerializer

from rest_framework.decorators import api_view

from django.db import transaction

from .services.payment_service import (
    PaymentGatewayError,
    initiate_payment,
)

import requests

logger = logging.getLogger(__name__)

class BookingCreateView(APIView):

    def post(self, request):
        serializer = BookingRequestSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking = serializer.save()

        try:
            payment_result = initiate_payment(
                booking_id=booking.id,
                amount=500,
            )

        except PaymentGatewayError as exc:
            return Response(
                {
                    "error": str(exc),
                    "booking_id": booking.id,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "booking": BookingRequestSerializer(
                    booking
                ).data,
                "payment": payment_result,
            },
            status=status.HTTP_201_CREATED,
        )

class LSASearchView(APIView):

    def get(self, request):
        skill = request.query_params.get("skill")
        start_time = request.query_params.get("start_time")
        end_time = request.query_params.get("end_time")

        if not skill:
            return Response(
                {"error": "skill is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not start_time or not end_time:
            return Response(
                {
                    "error": (
                        "start_time and end_time are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_time = parse_datetime(start_time)
        end_time = parse_datetime(end_time)

        if not start_time or not end_time:
            return Response(
                {"error": "Invalid datetime format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if start_time >= end_time:
            return Response(
                {
                    "error": (
                        "start_time must be earlier than end_time."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        overlapping_bookings = BookingRequest.objects.filter(
            lsa=OuterRef("pk"),
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=[
                BookingRequest.Status.PENDING,
                BookingRequest.Status.CONFIRMED,
            ],
        )

        lsas = (
            LSAProfile.objects
            .filter(
                is_active=True,
                skills__contains=[skill.lower()],
            )
            .annotate(
                has_overlap=Exists(overlapping_bookings)
            )
            .filter(has_overlap=False)
        )

        serializer = LSASearchSerializer(lsas, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

@api_view(["POST"])
def mock_payment_charge(request):
    booking_id = request.data.get("booking_id")
    amount = request.data.get("amount")

    if not booking_id or not amount:
        return Response(
            {
                "error": (
                    "booking_id and amount are required."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    success = float(amount) % 1 != 0.99

    payment_status = "success" if success else "failed"

    webhook_url = (
        "http://127.0.0.1:8000/"
        "api/v1/payments/webhook/"
    )

    try:
        requests.post(
            webhook_url,
            json={
                "booking_id": booking_id,
                "status": payment_status,
            },
            timeout=5,
        )
    except requests.RequestException:
        logger.exception(
            "Failed to send payment webhook."
        )

    response_status = (
        status.HTTP_200_OK
        if success
        else status.HTTP_402_PAYMENT_REQUIRED
    )

    return Response(
        {
            "payment_id": f"pay_{booking_id}",
            "booking_id": booking_id,
            "status": payment_status,
            "amount": amount,
        },
        status=response_status,
    )

@api_view(["POST"])
def payment_webhook(request):
    booking_id = request.data.get("booking_id")
    payment_status = request.data.get("status")

    if not booking_id or not payment_status:
        return Response(
            {
                "error": (
                    "booking_id and status are required."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if payment_status not in ["success", "failed"]:
        return Response(
            {"error": "Invalid payment status."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            booking = BookingRequest.objects.select_for_update().get(
                id=booking_id
            )

            if payment_status == "success":
                booking.status = BookingRequest.Status.CONFIRMED
            else:
                booking.status = (
                    BookingRequest.Status.PAYMENT_FAILED
                )

            booking.save(
                update_fields=["status"]
            )

    except BookingRequest.DoesNotExist:
        return Response(
            {"error": "Booking not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "booking_id": booking.id,
            "status": booking.status,
        },
        status=status.HTTP_200_OK,
    )