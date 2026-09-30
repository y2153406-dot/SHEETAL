from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import signing
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from urllib.parse import urlencode

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    EmergencyAlert,
    EmergencyIncident,
    SafetyContact,
    ShieldDevice,
    LiveLocation,
)
from .serializers import EmergencyIncidentSerializer
from .services import send_incident_alerts


def home(request):
    return render(request, "home.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            user = None

        if user is not None and user.check_password(password):
            login(request, user)
            return redirect("dashboard")

        return render(
            request,
            "login.html",
            {"error": "Invalid email or password."},
        )

    return render(request, "login.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not full_name or not email or not password:
            return render(
                request,
                "register.html",
                {"error": "Please fill all required fields."},
            )

        if password != confirm_password:
            return render(
                request,
                "register.html",
                {"error": "Passwords do not match."},
            )

        if User.objects.filter(username=email).exists():
            return render(
                request,
                "register.html",
                {"error": "An account with this email already exists."},
            )

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name,
        )

        login(request, user)
        return redirect("dashboard")

    return render(request, "register.html")


@login_required
def dashboard(request):
    incidents = EmergencyIncident.objects.filter(
        user=request.user
    ).order_by("-created_at")

    active_incident = incidents.filter(
        status__in=[
            "active",
            "acknowledged",
            "escalated",
        ]
    ).first()

    safety_contacts = SafetyContact.objects.filter(
        user=request.user
    ).order_by("-created_at")

    active_contacts = safety_contacts.filter(
        is_active=True
    )

    return render(
        request,
        "dashboard.html",
        {
            "incidents": incidents,
            "active_incident": active_incident,
            "safety_contacts": safety_contacts,
            "active_contacts": active_contacts,
        },
    )


@login_required
def emergency_response(request, incident_id):
    incident = EmergencyIncident.objects.filter(
        id=incident_id,
        user=request.user,
    ).first()

    if incident is None:
        return redirect("dashboard")

    alerts = EmergencyAlert.objects.filter(
        incident=incident,
    ).select_related("contact").order_by("created_at")

    return render(
        request,
        "emergency_response.html",
        {
            "incident": incident,
            "alerts": alerts,
        },
    )


@login_required
def acknowledge_emergency(request, incident_id):
    if request.method != "POST":
        return redirect(
            "emergency_response",
            incident_id=incident_id,
        )

    incident = EmergencyIncident.objects.filter(
        id=incident_id,
        user=request.user,
    ).first()

    if incident is None:
        return redirect("dashboard")

    if incident.status == "active":
        incident.status = "acknowledged"
        incident.acknowledged_at = timezone.now()

        incident.save(
            update_fields=[
                "status",
                "acknowledged_at",
            ]
        )

    return redirect(
        "emergency_response",
        incident_id=incident.id,
    )


@login_required
def resolve_emergency(request, incident_id):
    if request.method != "POST":
        return redirect(
            "emergency_response",
            incident_id=incident_id,
        )

    incident = EmergencyIncident.objects.filter(
        id=incident_id,
        user=request.user,
    ).first()

    if incident is None:
        return redirect("dashboard")

    if incident.status != "resolved":
        incident.status = "resolved"
        incident.resolved_at = timezone.now()

        if incident.acknowledged_at is None:
            incident.acknowledged_at = timezone.now()

        incident.save(
            update_fields=[
                "status",
                "acknowledged_at",
                "resolved_at",
            ]
        )

    return redirect(
        "emergency_response",
        incident_id=incident.id,
    )


@login_required
def safety_circle(request):
    contacts = SafetyContact.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "safety_circle.html",
        {
            "contacts": contacts,
        },
    )


@login_required
def add_safety_contact(request):
    if request.method != "POST":
        return redirect("safety_circle")

    name = request.POST.get("name", "").strip()
    phone = request.POST.get("phone", "").strip()
    email = request.POST.get("email", "").strip()
    relationship = request.POST.get("relationship", "").strip()

    if not name or not phone:
        return render(
            request,
            "safety_circle.html",
            {
                "contacts": SafetyContact.objects.filter(
                    user=request.user
                ).order_by("-created_at"),
                "error": "Name and phone number are required.",
            },
        )

    SafetyContact.objects.create(
        user=request.user,
        name=name,
        phone=phone,
        email=email,
        relationship=relationship,
        is_active=True,
    )

    return redirect("safety_circle")


@login_required
def delete_safety_contact(request, contact_id):
    if request.method == "POST":
        SafetyContact.objects.filter(
            id=contact_id,
            user=request.user,
        ).delete()

    return redirect("safety_circle")


def logout_view(request):
    logout(request)
    return redirect("home")


def api_health(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "Guardian SHIELD API",
        }
    )


@api_view(["POST"])
def create_emergency(request):
    if not request.user.is_authenticated:
        return Response(
            {
                "status": "error",
                "message": "Authentication required.",
            },
            status=401,
        )

    data = request.data.copy()

    if not data.get("trigger_type"):
        data["trigger_type"] = data.get("type", "test")

    if not data.get("message"):
        data["message"] = (
            "Emergency alert triggered from Guardian SHIELD."
        )

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    try:
        if latitude not in ["", None]:
            data["latitude"] = f"{float(latitude):.7f}"
        else:
            data["latitude"] = None

        if longitude not in ["", None]:
            data["longitude"] = f"{float(longitude):.7f}"
        else:
            data["longitude"] = None

    except (TypeError, ValueError):
        return Response(
            {
                "status": "error",
                "message": "Invalid GPS coordinates.",
            },
            status=400,
        )

    serializer = EmergencyIncidentSerializer(data=data)

    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "message": "Emergency data validation failed.",
                "errors": serializer.errors,
            },
            status=400,
        )

    incident = serializer.save(
        user=request.user,
        status="active",
    )

    # ---------------------------------------------------------
    # CREATE SECURE INDIVIDUAL PARENT EMERGENCY LINK
    # ---------------------------------------------------------

    emergency_token = signing.dumps(
        {"incident_id": incident.id},
        salt="shield-parent-emergency",
    )

    parent_path = reverse(
        "parent_emergency",
        args=[incident.id],
    )

    parent_url = request.build_absolute_uri(
        f"{parent_path}?{urlencode({'token': emergency_token})}"
    )

    # ---------------------------------------------------------
    # CREATE SECURE PARENT DASHBOARD LINK
    # ---------------------------------------------------------

    parent_dashboard_token = signing.dumps(
        {"user_id": request.user.id},
        salt="shield-parent-dashboard",
    )

    parent_dashboard_path = reverse(
        "parent_dashboard",
    )

    parent_dashboard_url = request.build_absolute_uri(
        f"{parent_dashboard_path}?{urlencode({'token': parent_dashboard_token})}"
    )

    # ---------------------------------------------------------
    # GET ACTIVE SAFETY CIRCLE CONTACTS
    # ---------------------------------------------------------

    active_contacts = SafetyContact.objects.filter(
        user=request.user,
        is_active=True,
    )

    # ---------------------------------------------------------
    # BUILD EMERGENCY MESSAGE
    # ---------------------------------------------------------

    alert_message = (
        f"GUARDIAN SHIELD EMERGENCY\n"
        f"{request.user.first_name or request.user.username} "
        f"has triggered an emergency alert."
    )

    if (
        incident.latitude is not None
        and incident.longitude is not None
    ):
        alert_message += (
            f"\n\nLocation:\n"
            f"https://maps.google.com/?q="
            f"{incident.latitude},{incident.longitude}"
        )

    alert_message += (
        f"\n\nParent Live Tracking Dashboard:\n"
        f"{parent_dashboard_url}"
    )

    # ---------------------------------------------------------
    # CREATE ALERT FOR EVERY ACTIVE CONTACT
    # ---------------------------------------------------------

    for contact in active_contacts:
        EmergencyAlert.objects.create(
            incident=incident,
            contact=contact,
            channel="sms",
            status="pending",
            message=alert_message,
        )

    # ---------------------------------------------------------
    # SEND ALL PENDING ALERTS
    # ---------------------------------------------------------

    alert_result = send_incident_alerts(incident)

    alerts_created = alert_result["total"]
    alerts_sent = alert_result["sent"]
    alerts_failed = alert_result["failed"]

    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    return Response(
        {
            "status": "success",
            "message": "Emergency incident created successfully.",
            "incident_id": incident.id,
            "incident_status": incident.status,
            "trigger_type": incident.trigger_type,
            "latitude": incident.latitude,
            "longitude": incident.longitude,

            "parent_emergency_url": parent_url,

            "parent_dashboard_url": parent_dashboard_url,

            "alerts_created": alerts_created,
            "alerts_sent": alerts_sent,
            "alerts_failed": alerts_failed,
            "created_at": incident.created_at,
        },
        status=201,
    )


def parent_emergency(request, incident_id):
    """
    Secure parent-facing emergency page.

    Parent does not need a SHIELD account.
    Access is granted through a signed emergency token.
    """

    token = request.GET.get("token")

    if not token:
        return render(
            request,
            "parent_emergency.html",
            {
                "error": "Invalid or missing emergency access link."
            },
            status=403,
        )

    try:
        token_data = signing.loads(
            token,
            salt="shield-parent-emergency",
            max_age=60 * 60 * 24,
        )

        if token_data.get("incident_id") != incident_id:
            raise signing.BadSignature

    except (
        signing.BadSignature,
        signing.SignatureExpired,
    ):
        return render(
            request,
            "parent_emergency.html",
            {
                "error": "This emergency link is invalid or has expired."
            },
            status=403,
        )

    incident = get_object_or_404(
        EmergencyIncident.objects.select_related("user"),
        id=incident_id,
    )

    return render(
        request,
        "parent_emergency.html",
        {
            "incident": incident,
            "user": incident.user,
        },
    )


@api_view(["POST"])
def update_live_location(request):
    if not request.user.is_authenticated:
        return Response(
            {
                "status": "error",
                "message": "Authentication required.",
            },
            status=401,
        )

    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")
    accuracy = request.data.get("accuracy")

    if latitude in ["", None] or longitude in ["", None]:
        return Response(
            {
                "status": "error",
                "message": "Latitude and longitude are required.",
            },
            status=400,
        )

    try:
        latitude = f"{float(latitude):.7f}"
        longitude = f"{float(longitude):.7f}"

        if accuracy not in ["", None]:
            accuracy = float(accuracy)
        else:
            accuracy = None

    except (TypeError, ValueError):
        return Response(
            {
                "status": "error",
                "message": "Invalid location data.",
            },
            status=400,
        )

    location, created = LiveLocation.objects.update_or_create(
        user=request.user,
        defaults={
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy,
            "is_tracking": True,
        },
    )

    return Response(
        {
            "status": "success",
            "message": "Live location updated successfully.",
            "latitude": location.latitude,
            "longitude": location.longitude,
            "accuracy": location.accuracy,
            "is_tracking": location.is_tracking,
            "updated_at": location.updated_at,
        },
        status=201 if created else 200,
    )


@api_view(["GET"])
def get_live_location(request):
    if not request.user.is_authenticated:
        return Response(
            {
                "status": "error",
                "message": "Authentication required.",
            },
            status=401,
        )

    location = LiveLocation.objects.filter(
        user=request.user
    ).first()

    if location is None:
        return Response(
            {
                "status": "error",
                "message": "No live location available.",
            },
            status=404,
        )

    return Response(
        {
            "status": "success",
            "latitude": location.latitude,
            "longitude": location.longitude,
            "accuracy": location.accuracy,
            "is_tracking": location.is_tracking,
            "updated_at": location.updated_at,
        },
        status=200,
    )


@login_required
def live_location(request):
    return render(
        request,
        "live_location.html",
    )


@api_view(["GET"])
def parent_live_location(request, incident_id):
    token = request.GET.get("token")

    if not token:
        return Response(
            {
                "status": "error",
                "message": "Invalid or missing access token.",
            },
            status=403,
        )

    try:
        token_data = signing.loads(
            token,
            salt="shield-parent-emergency",
            max_age=60 * 60 * 24,
        )

        if token_data.get("incident_id") != incident_id:
            raise signing.BadSignature

    except (
        signing.BadSignature,
        signing.SignatureExpired,
    ):
        return Response(
            {
                "status": "error",
                "message": "This emergency access link is invalid or expired.",
            },
            status=403,
        )

    incident = get_object_or_404(
        EmergencyIncident,
        id=incident_id,
    )

    location = LiveLocation.objects.filter(
        user=incident.user
    ).first()

    if location is None:
        return Response(
            {
                "status": "error",
                "message": "Live location is not available yet.",
            },
            status=404,
        )

    return Response(
        {
            "status": "success",
            "incident_id": incident.id,
            "user": (
                incident.user.first_name
                or incident.user.username
            ),
            "latitude": location.latitude,
            "longitude": location.longitude,
            "accuracy": location.accuracy,
            "is_tracking": location.is_tracking,
            "updated_at": location.updated_at,
        },
        status=200,
    )


def parent_dashboard(request):
    """
    Secure parent dashboard.

    Parent does not need a SHIELD account.
    Access is granted through a signed dashboard token.
    """

    token = request.GET.get("token")

    if not token:
        return render(
            request,
            "parent_dashboard.html",
            {
                "error": "Invalid or missing parent access link."
            },
            status=403,
        )

    try:
        token_data = signing.loads(
            token,
            salt="shield-parent-dashboard",
            max_age=60 * 60 * 24,
        )

        user_id = token_data.get("user_id")

        if not user_id:
            raise signing.BadSignature

    except (
        signing.BadSignature,
        signing.SignatureExpired,
    ):
        return render(
            request,
            "parent_dashboard.html",
            {
                "error": "This parent dashboard link is invalid or has expired."
            },
            status=403,
        )

    parent_user = get_object_or_404(
        User,
        id=user_id,
    )

    incidents = EmergencyIncident.objects.filter(
        user=parent_user
    ).order_by("-created_at")

    # ---------------------------------------------------------
    # CREATE INDIVIDUAL SECURE LINKS FOR EVERY INCIDENT
    # ---------------------------------------------------------

    incident_links = {}

    for incident in incidents:
        incident_token = signing.dumps(
            {"incident_id": incident.id},
            salt="shield-parent-emergency",
        )

        incident_path = reverse(
            "parent_emergency",
            args=[incident.id],
        )

        incident_links[incident.id] = (
            f"{incident_path}?{urlencode({'token': incident_token})}"
        )

    return render(
        request,
        "parent_dashboard.html",
        {
            "incidents": incidents,
            "parent_user": parent_user,
            "token": token,
            "incident_links": incident_links,
        },
    )