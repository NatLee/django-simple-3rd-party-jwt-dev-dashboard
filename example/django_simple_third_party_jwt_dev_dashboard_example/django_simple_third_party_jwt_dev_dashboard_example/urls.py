"""URLs of the example project, the same as the README's quick start."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

dashboard_urls = settings.DEV_DASHBOARD_SETTINGS

urlpatterns = [
    path("admin/", admin.site.urls),
    # The dashboard, Simple JWT's token views, and the Google and Microsoft routes
    path("", include("django_simple_third_party_jwt_dev_dashboard.all_urls")),
]

# Optional Swagger and Redoc pages. To try them: add "drf_yasg" to INSTALLED_APPS,
# uncomment swagger_url and redoc_url in DEV_DASHBOARD_SETTINGS, and uncomment this block.
#
# from drf_yasg import openapi
# from drf_yasg.views import get_schema_view
# from rest_framework.permissions import AllowAny
#
# schema_view = get_schema_view(
#     openapi.Info(title="DEV DASHBOARD API", default_version="v1", description="DEV API"),
#     public=True,
#     permission_classes=(AllowAny,),  # or (IsAdminUser,) to allow staff only
# )
# urlpatterns += [
#     path(dashboard_urls['swagger_url'] + "/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
#     path(dashboard_urls['redoc_url'] + "/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
# ]
