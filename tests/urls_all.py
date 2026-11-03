"""The README's quick-start urls.py: one include for the dashboard, plus the project's own admin."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("django_simple_third_party_jwt_dev_dashboard.all_urls")),
    path("api/__hidden_admin/", admin.site.urls),
]
