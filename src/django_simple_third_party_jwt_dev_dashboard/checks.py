"""Startup checks that explain a dashboard setup which cannot work.

Django runs them on ``manage.py check``, ``runserver`` and ``migrate``. They only look at a
project that serves the dashboard: if its URLs are not included (for example because the
project adds them only while DEBUG is on), there is nothing to report. Every message is a
warning, so the project still starts; silence one with ``SILENCED_SYSTEM_CHECKS``.
"""
from typing import Any, List, Optional

from django.apps import apps
from django.conf import settings
from django.core import checks
from django.urls import NoReverseMatch, Resolver404, get_script_prefix, resolve, reverse

ALL_URLS = "django_simple_third_party_jwt_dev_dashboard.all_urls"
REQUEST_CONTEXT_PROCESSOR = "django.template.context_processors.request"
DJANGO_TEMPLATES = "django.template.backends.django.DjangoTemplates"

# DEV_DASHBOARD_SETTINGS keys the JavaScript posts to: (key, what calls it, Simple JWT view).
JWT_URLS = (
    ("jwt_token_url", "the JWT Login button", "TokenObtainPairView"),
    ("jwt_refresh_url", "the token refresh on every dashboard visit", "TokenRefreshView"),
    ("jwt_verify_url", "the token check after every login", "TokenVerifyView"),
)
# Navbar links to pages the project serves itself: (key, link text).
LINK_URLS = (("admin_url", "Admin"), ("swagger_url", "Swagger"), ("redoc_url", "Redoc"))


def _is_served(path: str) -> bool:
    """True if the project's URLconf answers `path`, with or without a trailing slash."""
    for candidate in (path, path.rstrip("/") + "/"):
        try:
            resolve(candidate)
            return True
        except Resolver404:
            pass
    return False


def _dashboard_path() -> Optional[str]:
    """Where the dashboard is mounted, like "/api/__hidden_dev_dashboard/", or None."""
    try:
        path = reverse("dev-dashboard")
    except NoReverseMatch:
        return None
    except Exception:  # A broken URLconf is reported by Django's own URL checks.
        return None
    prefix = get_script_prefix()
    return "/" + path[len(prefix):] if path.startswith(prefix) else path


def _warning(message: str, hint: str, number: int) -> checks.Warning:
    return checks.Warning(message, hint=hint, id="dev_dashboard.W%03d" % number)


@checks.register(checks.Tags.urls)
def check_dashboard_setup(app_configs: Any = None, **kwargs: Any) -> List[checks.CheckMessage]:
    mounted_at = _dashboard_path()
    if mounted_at is None:
        return []

    # The values the pages really use (see views.dev_dashboard_setting).
    from django_simple_third_party_jwt_dev_dashboard.views import dev_dashboard_setting as pages

    found = []

    if not apps.is_installed("django_simple_third_party_jwt"):
        found.append(_warning(
            "'django_simple_third_party_jwt' is not in INSTALLED_APPS.",
            "The Google and Microsoft logins keep their accounts in its tables. Add it to "
            "INSTALLED_APPS and run `manage.py migrate`.",
            1,
        ))

    engines = [engine for engine in settings.TEMPLATES if engine.get("BACKEND") == DJANGO_TEMPLATES]
    if engines and not any(
        REQUEST_CONTEXT_PROCESSOR in engine.get("OPTIONS", {}).get("context_processors", ())
        for engine in engines
    ):
        found.append(_warning(
            "The dashboard cannot tell who is logged in: the request context processor is missing.",
            "Add %r to TEMPLATES[...]['OPTIONS']['context_processors'] (new Django projects have it)."
            % REQUEST_CONTEXT_PROCESSOR,
            2,
        ))

    expected = "/%s/" % pages["dashboard_url"]
    if mounted_at != expected:
        found.append(_warning(
            "The dashboard is served at %s, but DEV_DASHBOARD_SETTINGS['dashboard_url'] is %r."
            % (mounted_at, pages["dashboard_url"]),
            "Its pages link and post to %s. Set dashboard_url to %r, or include the dashboard's "
            "URLs at %r." % (expected, mounted_at.strip("/"), pages["dashboard_url"] + "/"),
            3,
        ))

    for key, caller, view in JWT_URLS:
        if not pages[key]:
            found.append(_warning(
                "DEV_DASHBOARD_SETTINGS has no %r, so %s has nowhere to go." % (key, caller),
                "Add %r with the path of Simple JWT's %s, such as %r." % (key, view, "api/auth/token"),
                4,
            ))
        elif not _is_served("/" + pages[key]):
            found.append(_warning(
                "Nothing is served at /%s (DEV_DASHBOARD_SETTINGS[%r]), which %s calls."
                % (pages[key], key, caller),
                "Serve Simple JWT's %s there, or include %r in your urls.py to get all of the "
                "dashboard's URLs at once." % (view, ALL_URLS),
                4,
            ))

    prefix = pages["third_party_jwt_url"]
    if not prefix:
        found.append(_warning(
            "JWT_3RD_PREFIX is empty, so the Google and Microsoft buttons call //auth/..., "
            "which the browser treats as another website.",
            "Set JWT_3RD_PREFIX to a prefix such as 'api'.",
            5,
        ))
    elif not _is_served("/%s/auth/google/token" % prefix):
        found.append(_warning(
            "Nothing is served at /%s/auth/google/token, which the Google button calls." % prefix,
            "Include 'django_simple_third_party_jwt.urls' (or %r) in your urls.py." % ALL_URLS,
            5,
        ))

    for key, label in LINK_URLS:
        if pages[key] and not _is_served("/" + pages[key]):
            found.append(_warning(
                "The navbar's %s link goes to /%s, but nothing is served there." % (label, pages[key]),
                "Serve that page there or change DEV_DASHBOARD_SETTINGS[%r]. A key left out of "
                "DEV_DASHBOARD_SETTINGS hides its link; without the setting, the dashboard links "
                "to api/__hidden_admin, api/__hidden_swagger and api/__hidden_redoc." % key,
                6,
            ))

    return found
