"""Every URL the dashboard needs, in one include.

In the project's ``urls.py``::

    urlpatterns += [
        path("", include("django_simple_third_party_jwt_dev_dashboard.all_urls")),
    ]

That serves, at the paths from ``DEV_DASHBOARD_SETTINGS`` and ``JWT_3RD_PREFIX``:

- the dashboard with its login and logout pages (this package's ``urls.py``),
- Simple JWT's token, refresh and verify views, which the dashboard's buttons call,
- django-simple-third-party-jwt's Google and Microsoft login routes.

The Admin, Swagger and Redoc links are not served here: they point at pages your project
serves itself, so set ``admin_url`` to wherever your admin lives.
"""
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from django_simple_third_party_jwt_dev_dashboard.settings import DEV_DASHBOARD_SETTINGS

# (DEV_DASHBOARD_SETTINGS key, Simple JWT view, URL name); the names match the README's
# hand-written urls.py, so code that reverses them keeps working after switching to this module.
SIMPLE_JWT_ROUTES = (
    ("jwt_token_url", TokenObtainPairView, "token_get"),
    ("jwt_refresh_url", TokenRefreshView, "token_refresh"),
    ("jwt_verify_url", TokenVerifyView, "token_verify"),
)

urlpatterns = [
    # Google and Microsoft login, under /<JWT_3RD_PREFIX>/auth/
    path("", include("django_simple_third_party_jwt.urls")),
]

if DEV_DASHBOARD_SETTINGS.get("dashboard_url"):
    urlpatterns.append(
        path(DEV_DASHBOARD_SETTINGS["dashboard_url"] + "/", include("django_simple_third_party_jwt_dev_dashboard.urls"))
    )

urlpatterns += [
    path(DEV_DASHBOARD_SETTINGS[key], view.as_view(), name=name)
    for key, view, name in SIMPLE_JWT_ROUTES
    if DEV_DASHBOARD_SETTINGS.get(key)
]
