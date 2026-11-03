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
from django.utils.module_loading import import_string

from django_simple_third_party_jwt_dev_dashboard.settings import DEV_DASHBOARD_SETTINGS, SIMPLE_JWT_URLS

urlpatterns = [
    # Google and Microsoft login, under /<JWT_3RD_PREFIX>/auth/
    path("", include("django_simple_third_party_jwt.urls")),
]

if DEV_DASHBOARD_SETTINGS.get("dashboard_url"):
    urlpatterns.append(
        path(DEV_DASHBOARD_SETTINGS["dashboard_url"] + "/", include("django_simple_third_party_jwt_dev_dashboard.urls"))
    )

urlpatterns += [
    path(DEV_DASHBOARD_SETTINGS[key], import_string(route.view).as_view(), name=route.url_name)
    for key, route in SIMPLE_JWT_URLS.items()
    if DEV_DASHBOARD_SETTINGS.get(key)
]
