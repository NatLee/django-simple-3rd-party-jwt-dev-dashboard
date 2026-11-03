"""Django settings for the test suite.

The dashboard part mirrors the "Quick Start" section of the README.
"""

SECRET_KEY = "test-only-key-long-enough-for-hs256-signing"
DEBUG = False
USE_TZ = True
ALLOWED_HOSTS = ["testserver", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "bootstrap3",
    "django_simple_third_party_jwt",
    "django_simple_third_party_jwt_dev_dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Dashboard settings, as in the README
DEV_DASHBOARD_SETTINGS = {
    "jwt_token_url": "api/auth/token",
    "jwt_refresh_url": "api/auth/token/refresh",
    "jwt_verify_url": "api/auth/token/verify",
    "dashboard_url": "api/__hidden_dev_dashboard",
    "admin_url": "api/__hidden_admin",
}
LOGIN_REDIRECT_URL = "/" + DEV_DASHBOARD_SETTINGS["dashboard_url"]
JWT_3RD_PREFIX = "api"

# SECURE_REFERRER_POLICY and SECURE_CROSS_ORIGIN_OPENER_POLICY keep Django's defaults: the
# dashboard sends the headers Google Sign-In needs on its own pages.

# Placeholder third-party login values; nothing here talks to Google or Microsoft.
SOCIAL_GOOGLE_CLIENT_ID = "test-google-client-id.apps.googleusercontent.com"
SOCIAL_MICROSOFT_CLIENT_ID = "test-microsoft-client-id"
SOCIAL_MICROSOFT_CLIENT_SECRET = "test-microsoft-client-secret"
VALID_REGISTER_DOMAINS = ["example.com"]
