from django.contrib import admin

from .models import (
    EmergencyAlert,
    EmergencyIncident,
    SafetyContact,
    ShieldDevice,
)


@admin.register(SafetyContact)
class SafetyContactAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "email",
        "relationship",
        "is_active",
        "user",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "phone",
        "email",
        "user__username",
    )


@admin.register(ShieldDevice)
class ShieldDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "device_id",
        "user",
        "battery_level",
        "gps_status",
        "gsm_status",
        "is_online",
        "last_seen",
    )

    list_filter = (
        "gps_status",
        "gsm_status",
        "is_online",
    )

    search_fields = (
        "device_id",
        "user__username",
    )


@admin.register(EmergencyIncident)
class EmergencyIncidentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "trigger_type",
        "status",
        "latitude",
        "longitude",
        "created_at",
    )

    list_filter = (
        "trigger_type",
        "status",
    )

    search_fields = (
        "user__username",
        "message",
    )

    ordering = (
        "-created_at",
    )


@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "incident",
        "contact",
        "channel",
        "status",
        "sent_at",
        "created_at",
    )

    list_filter = (
        "channel",
        "status",
    )

    search_fields = (
        "contact__name",
        "contact__phone",
        "incident__user__username",
        "message",
    )

    ordering = (
        "-created_at",
    )