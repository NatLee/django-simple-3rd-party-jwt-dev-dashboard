"""URL configuration for the test suite, following the README's `urls.py` section."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # third-party login routes from django-simple-third-party-jwt
    path("", include("django_simple_third_party_jwt.urls")),
    # the dashboard
    path(
        settings.DEV_DASHBOARD_SETTINGS["dashboard_url"] + "/",
        include("django_simple_third_party_jwt_dev_dashboard.urls"),
    ),
    path(settings.DEV_DASHBOARD_SETTINGS["admin_url"] + "/", admin.site.urls),
    # Simple JWT
    path(settings.DEV_DASHBOARD_SETTINGS["jwt_token_url"], TokenObtainPairView.as_view(), name="token_get"),
    path(settings.DEV_DASHBOARD_SETTINGS["jwt_refresh_url"], TokenRefreshView.as_view(), name="token_refresh"),
    path(settings.DEV_DASHBOARD_SETTINGS["jwt_verify_url"], TokenVerifyView.as_view(), name="token_verify"),
]
