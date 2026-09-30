from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path(
        "parent-dashboard/",
        views.parent_dashboard,
        name="parent_dashboard",
    ),

    path(
        "safety-circle/",
        views.safety_circle,
        name="safety_circle",
    ),
    path(
        "safety-circle/add/",
        views.add_safety_contact,
        name="add_safety_contact",
    ),
    path(
        "safety-circle/delete/<int:contact_id>/",
        views.delete_safety_contact,
        name="delete_safety_contact",
    ),

    path(
        "api/health/",
        views.api_health,
        name="api_health",
    ),

    path(
        "api/emergency/",
        views.create_emergency,
        name="create_emergency",
    ),

    path(
        "emergency-response/<int:incident_id>/",
        views.emergency_response,
        name="emergency_response",
    ),

    path(
        "emergency-response/<int:incident_id>/acknowledge/",
        views.acknowledge_emergency,
        name="acknowledge_emergency",
    ),

    path(
        "emergency-response/<int:incident_id>/resolve/",
        views.resolve_emergency,
        name="resolve_emergency",
    ),

    path(
        "emergency/<int:incident_id>/parent/",
        views.parent_emergency,
        name="parent_emergency",
    ),

    path(
        "api/live-location/",
        views.update_live_location,
        name="update_live_location",
    ),

    path(
        "api/live-location/current/",
        views.get_live_location,
        name="get_live_location",
    ),

    path(
        "live-location/",
        views.live_location,
        name="live_location",
    ),

    path(
        "api/live-location/<int:incident_id>/",
        views.parent_live_location,
        name="parent_live_location",
    ),
]