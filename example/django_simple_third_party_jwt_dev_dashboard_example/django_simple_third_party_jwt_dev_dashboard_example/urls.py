"""URLs of the example project, the same as the README's `urls.py` section."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

dashboard_urls = settings.DEV_DASHBOARD_SETTINGS

urlpatterns = [
    # Google and Microsoft login (django-simple-third-party-jwt)
    path("", include("django_simple_third_party_jwt.urls")),
    # The dev dashboard
    path(dashboard_urls['dashboard_url'] + "/", include("django_simple_third_party_jwt_dev_dashboard.urls")),
    path(dashboard_urls['admin_url'] + "/", admin.site.urls),
    # Simple JWT
    path(dashboard_urls['jwt_token_url'], TokenObtainPairView.as_view(), name="token-get"),
    path(dashboard_urls['jwt_refresh_url'], TokenRefreshView.as_view(), name="token-refresh"),
    path(dashboard_urls['jwt_verify_url'], TokenVerifyView.as_view(), name="token-verify"),
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
