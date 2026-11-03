"""all_urls: every URL the dashboard needs, in one include."""
import importlib
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from django_simple_third_party_jwt_dev_dashboard.checks import check_dashboard_setup

DASHBOARD = "/api/__hidden_dev_dashboard/"


@override_settings(ROOT_URLCONF="tests.urls_all")
class AllUrlsTests(TestCase):
    """tests/urls_all.py is the README's one-line urls.py: include(...all_urls) plus the admin."""

    def test_dashboard_and_login_pages_are_served(self):
        self.assertEqual(self.client.get(DASHBOARD).status_code, 200)
        self.assertEqual(self.client.get(DASHBOARD + "login").status_code, 200)

    def test_simple_jwt_views_are_served_at_the_configured_paths(self):
        User.objects.create_user("alice", password="s3cret-pass")

        tokens = self.client.post("/api/auth/token", {"username": "alice", "password": "s3cret-pass"}).json()
        verify = self.client.post("/api/auth/token/verify", {"token": tokens["access"]})
        refresh = self.client.post("/api/auth/token/refresh", {"refresh": tokens["refresh"]})

        self.assertEqual(verify.status_code, 200)
        self.assertIn("access", refresh.json())

    def test_url_names_match_the_hand_written_urls_py(self):
        self.assertEqual(reverse("token_get"), "/api/auth/token")
        self.assertEqual(reverse("token_refresh"), "/api/auth/token/refresh")
        self.assertEqual(reverse("token_verify"), "/api/auth/token/verify")
        self.assertEqual(reverse("dev-dashboard"), DASHBOARD)

    def test_google_and_microsoft_routes_come_from_the_base_package(self):
        self.assertEqual(reverse("google-token"), "/api/auth/google/token")
        self.assertEqual(reverse("microsoft-signin"), "/api/auth/microsoft/signin")

    def test_the_setup_passes_the_startup_checks(self):
        self.assertEqual(check_dashboard_setup(), [])

    def test_routes_follow_dev_dashboard_settings(self):
        from django_simple_third_party_jwt_dev_dashboard import all_urls

        custom = {"dashboard_url": "dev", "jwt_token_url": "jwt/get", "jwt_refresh_url": "jwt/refresh"}
        with mock.patch("django_simple_third_party_jwt_dev_dashboard.settings.DEV_DASHBOARD_SETTINGS", custom):
            routes = [str(p.pattern) for p in importlib.reload(all_urls).urlpatterns]
        importlib.reload(all_urls)

        # The verify URL is left out of `custom`, so it is not served.
        self.assertEqual(routes, ["", "dev/", "jwt/get", "jwt/refresh"])
