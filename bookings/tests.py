from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Parent, LSAProfile, BookingRequest


class BookingAPITests(APITestCase):

    def setUp(self):
        self.parent = Parent.objects.create(
            name="Test Parent",
            email="parent@test.com",
            phone="9999999999",
        )

        self.lsa = LSAProfile.objects.create(
            name="Test LSA",
            email="lsa@test.com",
            skills=["python", "math"],
            is_active=True,
        )

        self.start_time = timezone.now() + timedelta(days=1)
        self.end_time = self.start_time + timedelta(hours=1)

    # 1. Successful booking creation
    @patch("bookings.views.initiate_payment")
    def test_create_booking_success(self, mock_payment):
        mock_payment.return_value = {
            "payment_id": "pay_test",
            "status": "pending",
        }

        response = self.client.post(
            "/api/v1/bookings/",
            {
                "parent": self.parent.id,
                "lsa": self.lsa.id,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            BookingRequest.objects.count(),
            1,
        )

        mock_payment.assert_called_once()

    # 2. Invalid time range must be rejected
    def test_booking_invalid_time_range(self):
        response = self.client.post(
            "/api/v1/bookings/",
            {
                "parent": self.parent.id,
                "lsa": self.lsa.id,
                "start_time": self.end_time.isoformat(),
                "end_time": self.start_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "start_time must be earlier than end_time.",
            str(response.data),
        )

    # 3. Overlapping booking must be rejected
    def test_double_booking_is_rejected(self):
        BookingRequest.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            start_time=self.start_time,
            end_time=self.end_time,
            status=BookingRequest.Status.CONFIRMED,
        )

        response = self.client.post(
            "/api/v1/bookings/",
            {
                "parent": self.parent.id,
                "lsa": self.lsa.id,
                "start_time": (
                    self.start_time + timedelta(minutes=30)
                ).isoformat(),
                "end_time": (
                    self.end_time + timedelta(minutes=30)
                ).isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "already booked",
            str(response.data),
        )

    # 4. LSA search by skill
    def test_lsa_search_by_skill(self):
        response = self.client.get(
            "/api/v1/lsas/search/",
            {
                "skill": "python",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["name"],
            "Test LSA",
        )

    # 5. LSA with overlapping booking must not appear
    def test_lsa_search_excludes_booked_lsa(self):
        BookingRequest.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            start_time=self.start_time,
            end_time=self.end_time,
            status=BookingRequest.Status.CONFIRMED,
        )

        response = self.client.get(
            "/api/v1/lsas/search/",
            {
                "skill": "python",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            0,
        )

    # 6. Missing search skill must be rejected
    def test_lsa_search_requires_skill(self):
        response = self.client.get(
            "/api/v1/lsas/search/",
            {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["error"],
            "skill is required.",
        )

    # 7. Payment webhook confirms booking
    def test_payment_webhook_success(self):
        booking = BookingRequest.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            start_time=self.start_time,
            end_time=self.end_time,
            status=BookingRequest.Status.PENDING,
        )

        response = self.client.post(
            "/api/v1/payments/webhook/",
            {
                "booking_id": booking.id,
                "status": "success",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            BookingRequest.Status.CONFIRMED,
        )

    # 8. Payment failure changes booking status
    def test_payment_webhook_failure(self):
        booking = BookingRequest.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            start_time=self.start_time,
            end_time=self.end_time,
            status=BookingRequest.Status.PENDING,
        )

        response = self.client.post(
            "/api/v1/payments/webhook/",
            {
                "booking_id": booking.id,
                "status": "failed",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            BookingRequest.Status.PAYMENT_FAILED,
        )