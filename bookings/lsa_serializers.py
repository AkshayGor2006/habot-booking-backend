from rest_framework import serializers

from .models import LSAProfile


class LSASearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = LSAProfile
        fields = [
            "id",
            "name",
            "email",
            "skills",
            "is_active",
        ]