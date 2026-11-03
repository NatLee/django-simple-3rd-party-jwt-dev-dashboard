"""URLs of the example project, the same as the README's quick start."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # The dashboard, Simple JWT's token views, the Google and Microsoft routes, and the
    # Swagger and Redoc pages when drf-yasg is installed (see settings.py)
    path("", include("django_simple_third_party_jwt_dev_dashboard.all_urls")),
]
