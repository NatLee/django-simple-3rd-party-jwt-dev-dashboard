"""Dashboard settings, read once from the project's Django settings."""
from django.conf import settings

# Paths without a leading slash. A project that sets DEV_DASHBOARD_SETTINGS replaces this
# whole dict; keys it leaves out are treated as empty.
DEV_DASHBOARD_SETTINGS = getattr(settings, "DEV_DASHBOARD_SETTINGS", {
    "jwt_token_url": "api/auth/token",
    "jwt_refresh_url": "api/auth/token/refresh",
    "jwt_verify_url": "api/auth/token/verify",
    "dashboard_url": "api/__hidden_dev_dashboard",
    "admin_url": "api/__hidden_admin",
    "swagger_url": "api/__hidden_swagger",
    "redoc_url": "api/__hidden_redoc",
})

# The dashboard builds its third-party login URLs from django-simple-third-party-jwt's own
# JWT_3RD_PREFIX setting; this copy is kept for code that imports it from here.
JWT_3RD_PREFIX = getattr(settings, "JWT_3RD_PREFIX", "api")
