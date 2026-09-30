from django.contrib.auth.models import User
from django.db import models


class ShieldDevice(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="shield_device",
    )
    device_id = models.CharField(max_length=100, unique=True)
    battery_level = models.PositiveIntegerField(default=100)
    gps_status = models.BooleanField(default=False)
    gsm_status = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.device_id


class SafetyContact(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="safety_contacts",
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class EmergencyIncident(models.Model):

    TRIGGER_CHOICES = [
        ("manual", "Manual SOS"),
        ("test", "Test Emergency"),
        ("device", "Device SOS"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("acknowledged", "Acknowledged"),
        ("escalated", "Escalated"),
        ("resolved", "Resolved"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="emergency_incidents",
    )

    device = models.ForeignKey(
        ShieldDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
    )

    trigger_type = models.CharField(
        max_length=20,
        choices=TRIGGER_CHOICES,
        default="manual",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )

    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Incident #{self.id} - {self.user.username}"


class EmergencyAlert(models.Model):

    CHANNEL_CHOICES = [
        ("sms", "SMS"),
        ("email", "Email"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    incident = models.ForeignKey(
        EmergencyIncident,
        on_delete=models.CASCADE,
        related_name="alerts",
    )

    contact = models.ForeignKey(
        SafetyContact,
        on_delete=models.CASCADE,
        related_name="emergency_alerts",
    )

    channel = models.CharField(
        max_length=10,
        choices=CHANNEL_CHOICES,
        default="sms",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
    )

    message = models.TextField(blank=True)

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"Alert #{self.id} - "
            f"Incident #{self.incident.id} - "
            f"{self.contact.name}"
        )


class LiveLocation(models.Model):
    """
    Stores the user's latest GPS location
    for real-time location tracking.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="live_location",
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
    )

    accuracy = models.FloatField(
        null=True,
        blank=True,
    )

    is_tracking = models.BooleanField(
        default=False,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.latitude}, {self.longitude}"
        )