"""The dashboard page and the session login and logout behind it."""
from functools import wraps
from typing import Any, Callable

from django.conf import settings as django_settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from django_simple_third_party_jwt import settings as jwt_settings
from django_simple_third_party_jwt_dev_dashboard import __version__
from django_simple_third_party_jwt_dev_dashboard.compat import legacy_context
from django_simple_third_party_jwt_dev_dashboard.settings import DEFAULT_DEV_DASHBOARD_SETTINGS, DEV_DASHBOARD_SETTINGS

# Paths the templates link to or call from JavaScript: every DEV_DASHBOARD_SETTINGS key.
# A key the project leaves out becomes "", which hides the matching navbar link.
URL_SETTING_KEYS = tuple(DEFAULT_DEV_DASHBOARD_SETTINGS)

# Template context shared by every page, built once when Django imports the views.
dev_dashboard_setting = {
    "social_google_client_id": jwt_settings.SOCIAL_GOOGLE_CLIENT_ID,
    "social_microsoft_client_id": jwt_settings.SOCIAL_MICROSOFT_CLIENT_ID,
    # localStorage keys for the tokens: the base package's Microsoft login writes to these.
    "access_token_key": jwt_settings.MICROSOFT_JWT_REDIRECT_ACCESS_TOKEN_KEY,
    "refresh_token_key": jwt_settings.MICROSOFT_JWT_REDIRECT_REFRESH_TOKEN_KEY,
    **{key: DEV_DASHBOARD_SETTINGS.get(key, "") for key in URL_SETTING_KEYS},
    "debug": django_settings.DEBUG,
    "dashboard_version": __version__,
    **legacy_context(),
}

# Sign in with Google needs both on the page that shows its button: Google checks the page's
# origin from the Referer, and its popup has to talk back to this window. Django's defaults
# ("same-origin" for both) block that. Sending them from the dashboard's own pages means the
# project no longer has to relax SECURE_REFERRER_POLICY and SECURE_CROSS_ORIGIN_OPENER_POLICY
# everywhere. The values are what those two settings gave in the README's earlier setup.
GOOGLE_SIGN_IN_HEADERS = {
    "Referrer-Policy": "no-referrer-when-downgrade",
    "Cross-Origin-Opener-Policy": "unsafe-none",
}


def allow_google_sign_in(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Send GOOGLE_SIGN_IN_HEADERS with the view's response (SecurityMiddleware keeps them)."""

    @wraps(view)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = view(request, *args, **kwargs)
        for header, value in GOOGLE_SIGN_IN_HEADERS.items():
            response[header] = value
        return response

    return wrapper


@allow_google_sign_in
def dashboard(request: HttpRequest) -> HttpResponse:
    """Show the client IDs, the JWT kept in the browser and the session state."""
    return render(request, "dashboard.html", dev_dashboard_setting)


@csrf_exempt
@allow_google_sign_in
def login(request: HttpRequest) -> HttpResponse:
    """Session login with username and password; the page also offers JWT login."""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect("dev-dashboard")
    else:
        form = AuthenticationForm(request)

    return render(request, "login.html", {**dev_dashboard_setting, "form": form})


@csrf_exempt
@login_required
def session_logout(request: HttpRequest) -> HttpResponse:
    """End the session and go back to the dashboard."""
    auth_logout(request)
    return redirect("dev-dashboard")
