"""Dashboard settings, read once from the project's Django settings."""
from typing import NamedTuple

from django.conf import settings

# Used when the project does not set DEV_DASHBOARD_SETTINGS. Paths without a leading slash.
DEFAULT_DEV_DASHBOARD_SETTINGS = {
    "jwt_token_url": "api/auth/token",
    "jwt_refresh_url": "api/auth/token/refresh",
    "jwt_verify_url": "api/auth/token/verify",
    "dashboard_url": "api/__hidden_dev_dashboard",
    "admin_url": "api/__hidden_admin",
    "swagger_url": "api/__hidden_swagger",
    "redoc_url": "api/__hidden_redoc",
}


class SimpleJwtUrl(NamedTuple):
    view: str  # dotted path of the Simple JWT view that must answer at the setting's path
    url_name: str  # the name all_urls gives the route (the README's hand-written urls.py uses it too)
    used_by: str  # what on the page calls it, for the startup checks' messages


# The DEV_DASHBOARD_SETTINGS keys the dashboard's JavaScript posts to. all_urls serves them and
# checks.py explains them, both from this table.
SIMPLE_JWT_URLS = {
    "jwt_token_url": SimpleJwtUrl(
        "rest_framework_simplejwt.views.TokenObtainPairView", "token_get", "the JWT Login button"
    ),
    "jwt_refresh_url": SimpleJwtUrl(
        "rest_framework_simplejwt.views.TokenRefreshView", "token_refresh", "the token refresh on every dashboard visit"
    ),
    "jwt_verify_url": SimpleJwtUrl(
        "rest_framework_simplejwt.views.TokenVerifyView", "token_verify", "the token check after every login"
    ),
}

# A project that sets DEV_DASHBOARD_SETTINGS replaces this whole dict; keys it leaves out are
# treated as empty.
DEV_DASHBOARD_SETTINGS = getattr(settings, "DEV_DASHBOARD_SETTINGS", dict(DEFAULT_DEV_DASHBOARD_SETTINGS))

# The dashboard builds its third-party login URLs from django-simple-third-party-jwt's own
# JWT_3RD_PREFIX setting; this copy is kept for code that imports it from here.
JWT_3RD_PREFIX = getattr(settings, "JWT_3RD_PREFIX", "api")
