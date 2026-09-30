from rest_framework import serializers

from .models import (
    EmergencyIncident,
    SafetyContact,
    ShieldDevice,
    LiveLocation,
)


class SafetyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyContact
        fields = "__all__"


class ShieldDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShieldDevice
        fields = "__all__"


class EmergencyIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyIncident
        fields = [
            "id",
            "user",
            "device",
            "trigger_type",
            "status",
            "latitude",
            "longitude",
            "message",
            "created_at",
            "acknowledged_at",
            "resolved_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "created_at",
            "acknowledged_at",
            "resolved_at",
        ]


class LiveLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveLocation
        fields = [
            "latitude",
            "longitude",
            "accuracy",
            "is_tracking",
            "updated_at",
        ]
        read_only_fields = [
            "updated_at",
        ]