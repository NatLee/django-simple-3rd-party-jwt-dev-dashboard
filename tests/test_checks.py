"""Startup checks that explain a dashboard setup which cannot work."""
import types
from unittest import mock

from django.contrib import admin
from django.core import checks
from django.test import SimpleTestCase, override_settings
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from django_simple_third_party_jwt_dev_dashboard import views
from django_simple_third_party_jwt_dev_dashboard.checks import check_dashboard_setup
from django_simple_third_party_jwt_dev_dashboard.settings import DEFAULT_DEV_DASHBOARD_SETTINGS, SIMPLE_JWT_URLS


def urlconf(*patterns):
    """A URLconf made on the spot, for override_settings(ROOT_URLCONF=...)."""
    module = types.ModuleType("made_up_urls")
    module.urlpatterns = list(patterns)
    return module


BASE_PACKAGE = path("", include("django_simple_third_party_jwt.urls"))
DASHBOARD_URLS = path("api/__hidden_dev_dashboard/", include("django_simple_third_party_jwt_dev_dashboard.urls"))
ADMIN = path("api/__hidden_admin/", admin.site.urls)
SIMPLE_JWT = [
    path("api/auth/token", TokenObtainPairView.as_view()),
    path("api/auth/token/refresh", TokenRefreshView.as_view()),
    path("api/auth/token/verify", TokenVerifyView.as_view()),
]


class StartupCheckTests(SimpleTestCase):
    def ids(self):
        return [message.id for message in check_dashboard_setup()]

    def test_readme_setup_has_nothing_to_report(self):
        # tests/urls.py is the README's hand-written urls.py.
        self.assertEqual(self.ids(), [])

    def test_django_runs_the_check(self):
        with override_settings(ROOT_URLCONF=urlconf(DASHBOARD_URLS, BASE_PACKAGE, ADMIN)):
            found = checks.run_checks(tags=[checks.Tags.urls])

        self.assertIn("dev_dashboard.W003", [message.id for message in found])

    def test_quiet_when_the_dashboard_is_not_served(self):
        # For example a project that adds the dashboard's URLs only while DEBUG is on.
        with override_settings(ROOT_URLCONF=urlconf(BASE_PACKAGE, *SIMPLE_JWT)):
            self.assertEqual(self.ids(), [])

    def test_dashboard_mounted_somewhere_else_is_fine(self):
        # The pages link to their own routes by name, so dashboard_url does not have to match.
        elsewhere = path("dev/", include("django_simple_third_party_jwt_dev_dashboard.urls"))
        with override_settings(ROOT_URLCONF=urlconf(elsewhere, BASE_PACKAGE, ADMIN, *SIMPLE_JWT)):
            self.assertEqual(self.ids(), [])

    def test_simple_jwt_urls_not_served(self):
        with override_settings(ROOT_URLCONF=urlconf(DASHBOARD_URLS, BASE_PACKAGE, ADMIN)):
            found = check_dashboard_setup()

        self.assertEqual([m.id for m in found], ["dev_dashboard.W003"] * 3)
        self.assertIn("/api/auth/token", found[0].msg)
        self.assertIn("JWT Login button", found[0].msg)
        self.assertIn("all_urls", found[0].hint)

    def test_simple_jwt_url_missing_from_the_settings(self):
        with mock.patch.dict(views.dev_dashboard_setting, {"jwt_verify_url": ""}):
            found = check_dashboard_setup()

        self.assertEqual([m.id for m in found], ["dev_dashboard.W003"])
        self.assertIn("'jwt_verify_url'", found[0].msg)

    def test_hint_suggests_the_default_path_of_the_missing_key(self):
        # It used to suggest "api/auth/token" for all three keys.
        for key in SIMPLE_JWT_URLS:
            with mock.patch.dict(views.dev_dashboard_setting, {key: ""}):
                (found,) = check_dashboard_setup()

            self.assertIn(repr(DEFAULT_DEV_DASHBOARD_SETTINGS[key]), found.hint, key)
            self.assertIn(SIMPLE_JWT_URLS[key].view.rsplit(".", 1)[-1], found.hint, key)

    def test_google_and_microsoft_routes_not_served(self):
        with override_settings(ROOT_URLCONF=urlconf(DASHBOARD_URLS, ADMIN, *SIMPLE_JWT)):
            found = check_dashboard_setup()

        self.assertEqual([m.id for m in found], ["dev_dashboard.W004"])
        self.assertIn("'google-token' or 'microsoft-signin'", found[0].msg)

    def test_google_and_microsoft_routes_anywhere_are_fine(self):
        # Whatever path JWT_3RD_PREFIX gives them, the pages find them by name.
        moved = path("elsewhere/", include("django_simple_third_party_jwt.urls"))
        with override_settings(ROOT_URLCONF=urlconf(DASHBOARD_URLS, moved, ADMIN, *SIMPLE_JWT)):
            self.assertEqual(self.ids(), [])

    def test_navbar_link_to_a_page_that_is_not_served(self):
        # The defaults link to Swagger and Redoc pages that a project may not have.
        with mock.patch.dict(views.dev_dashboard_setting, {"swagger_url": "api/__hidden_swagger"}):
            found = check_dashboard_setup()

        self.assertEqual([m.id for m in found], ["dev_dashboard.W005"])
        self.assertIn("Swagger link goes to /api/__hidden_swagger", found[0].msg)
        for key in ("admin_url", "swagger_url", "redoc_url"):
            self.assertIn(DEFAULT_DEV_DASHBOARD_SETTINGS[key], found[0].hint)

    def test_admin_link_with_or_without_trailing_slash_is_fine(self):
        # The admin is mounted at "api/__hidden_admin/"; the link has no slash (APPEND_SLASH redirects).
        self.assertTrue(views.dev_dashboard_setting["admin_url"].endswith("admin"))
        self.assertNotIn("dev_dashboard.W005", self.ids())

    def test_missing_request_context_processor(self):
        from django.conf import settings

        templates = [dict(settings.TEMPLATES[0], OPTIONS={"context_processors": []})]
        with override_settings(TEMPLATES=templates):
            found = check_dashboard_setup()

        self.assertEqual([m.id for m in found], ["dev_dashboard.W002"])

    def test_base_package_not_installed(self):
        with mock.patch("django_simple_third_party_jwt_dev_dashboard.checks.apps.is_installed", return_value=False):
            found = check_dashboard_setup()

        self.assertEqual([m.id for m in found], ["dev_dashboard.W001"])
        self.assertIn("migrate", found[0].hint)
