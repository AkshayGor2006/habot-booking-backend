from django.contrib.postgres.indexes import GinIndex
from django.db import models

class Parent(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return self.name


class LSAProfile(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    skills = models.JSONField(default=list)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            GinIndex(
                fields=["skills"],
                name="lsa_skills_gin_idx",
            ),
        ]

    def __str__(self):
        return self.name


class BookingRequest(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PAYMENT_FAILED = "PAYMENT_FAILED", "Payment Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    lsa = models.ForeignKey(
        LSAProfile,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["lsa", "start_time", "end_time"],
                name="booking_lsa_time_idx",
            ),
            models.Index(
                fields=["parent", "start_time"],
                name="booking_parent_time_idx",
            ),
            models.Index(
                fields=["status"],
                name="booking_status_idx",
            ),
        ]

    def __str__(self):
        return f"Booking #{self.id}"