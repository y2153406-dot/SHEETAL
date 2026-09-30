import os

from django.utils import timezone

from .models import EmergencyAlert


def normalize_phone_number(phone):
    """
    Convert an Indian 10-digit number into E.164 format.

    Examples:
        9876543210  -> +919876543210
        +919876543210 -> +919876543210
    """

    phone = str(phone).strip().replace(" ", "").replace("-", "")

    if phone.startswith("+"):
        return phone

    if len(phone) == 10:
        return f"+91{phone}"

    return phone


def send_emergency_alert(alert):
    """
    Send one EmergencyAlert through Twilio.
    """

    try:
        from twilio.rest import Client

        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_PHONE_NUMBER")

        if not account_sid or not auth_token or not from_number:
            raise RuntimeError(
                "Twilio credentials are not configured."
            )

        client = Client(
            account_sid,
            auth_token,
        )

        to_number = normalize_phone_number(
            alert.contact.phone
        )

        message = client.messages.create(
            body=alert.message,
            from_=from_number,
            to=to_number,
        )

        alert.status = "sent"
        alert.sent_at = timezone.now()
        alert.save(
            update_fields=[
                "status",
                "sent_at",
            ]
        )

        return True

    except Exception as error:
        print(
            f"Emergency SMS failed for "
            f"{alert.contact.name}: {error}"
        )

        alert.status = "failed"
        alert.save(
            update_fields=[
                "status",
            ]
        )

        return False


def send_incident_alerts(incident):
    """
    Send all pending alerts belonging to an emergency incident.
    """

    alerts = EmergencyAlert.objects.filter(
        incident=incident,
        status="pending",
    )

    sent_count = 0
    failed_count = 0

    for alert in alerts:
        if send_emergency_alert(alert):
            sent_count += 1
        else:
            failed_count += 1

    return {
        "sent": sent_count,
        "failed": failed_count,
        "total": sent_count + failed_count,
    }