from rest_framework import serializers

from .models import BookingRequest


class BookingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingRequest
        fields = [
            "id",
            "parent",
            "lsa",
            "start_time",
            "end_time",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
        ]

    def validate(self, attrs):
        start_time = attrs["start_time"]
        end_time = attrs["end_time"]

        if start_time >= end_time:
            raise serializers.ValidationError(
                "start_time must be earlier than end_time."
            )

        lsa = attrs["lsa"]

        overlapping_booking = BookingRequest.objects.filter(
            lsa=lsa,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=[
                BookingRequest.Status.PENDING,
                BookingRequest.Status.CONFIRMED,
            ],
        ).exists()

        if overlapping_booking:
            raise serializers.ValidationError(
                "The LSA is already booked during this time."
            )

        return attrs