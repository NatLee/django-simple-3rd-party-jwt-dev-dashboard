"""Every URL the dashboard needs, in one include.

In the project's ``urls.py``::

    urlpatterns += [
        path("", include("django_simple_third_party_jwt_dev_dashboard.all_urls")),
    ]

That serves, at the paths from ``DEV_DASHBOARD_SETTINGS`` and ``JWT_3RD_PREFIX``:

- the dashboard with its login and logout pages (this package's ``urls.py``),
- Simple JWT's token, refresh and verify views, which the dashboard's buttons call,
- django-simple-third-party-jwt's Google and Microsoft login routes,
- the Swagger and Redoc pages, when the project has drf-yasg (the ``[docs]`` extra) in
  INSTALLED_APPS. drf-yasg is not imported otherwise.

The Admin link is not served here: set ``admin_url`` to wherever your admin lives.
"""
from django.apps import apps
from django.urls import include, path
from django.utils.module_loading import import_string

from django_simple_third_party_jwt_dev_dashboard.settings import (
    API_DOCS_URLS,
    DEV_DASHBOARD_SETTINGS,
    SIMPLE_JWT_URLS,
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
    path(DEV_DASHBOARD_SETTINGS[key], import_string(route.view).as_view(), name=route.url_name)
    for key, route in SIMPLE_JWT_URLS.items()
    if DEV_DASHBOARD_SETTINGS.get(key)
]

# drf-yasg's pages need its templates, hence INSTALLED_APPS rather than "can it be imported".
if apps.is_installed("drf_yasg"):
    from drf_yasg import openapi
    from drf_yasg.views import get_schema_view
    from rest_framework.permissions import AllowAny

    # Like the rest of the dashboard: a development page on a hidden URL, open to anyone who finds it.
    schema_view = get_schema_view(
        openapi.Info(title="DEV DASHBOARD API", default_version="v1"),
        public=True,
        permission_classes=(AllowAny,),
    )
    urlpatterns += [
        path(DEV_DASHBOARD_SETTINGS[key] + "/", schema_view.with_ui(ui, cache_timeout=0), name=url_name)
        for key, (ui, url_name) in API_DOCS_URLS.items()
        if DEV_DASHBOARD_SETTINGS.get(key)
    ]
