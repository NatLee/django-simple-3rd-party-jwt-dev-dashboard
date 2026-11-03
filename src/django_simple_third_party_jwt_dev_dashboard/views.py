"""The dashboard page and the session login and logout behind it."""
from django.conf import settings as django_settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from django_simple_third_party_jwt import settings as jwt_settings
from django_simple_third_party_jwt_dev_dashboard.settings import DEV_DASHBOARD_SETTINGS

# Paths the templates link to or call from JavaScript, taken from DEV_DASHBOARD_SETTINGS.
# A missing key becomes "", which hides the matching navbar link.
URL_SETTING_KEYS = (
    "jwt_token_url",
    "jwt_refresh_url",
    "jwt_verify_url",
    "dashboard_url",
    "admin_url",
    "swagger_url",
    "redoc_url",
)

# Template context shared by every page, built once when Django imports the views.
dev_dashboard_setting = {
    "social_google_client_id": jwt_settings.SOCIAL_GOOGLE_CLIENT_ID,
    "social_microsoft_client_id": jwt_settings.SOCIAL_MICROSOFT_CLIENT_ID,
    "third_party_jwt_url": jwt_settings.JWT_3RD_PREFIX,
    **{key: DEV_DASHBOARD_SETTINGS.get(key, "") for key in URL_SETTING_KEYS},
    "debug": django_settings.DEBUG,
}


def dashboard(request: HttpRequest) -> HttpResponse:
    """Show the client IDs, the JWT kept in the browser and the session state."""
    return render(request, "dashboard.html", dev_dashboard_setting)


@csrf_exempt
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
