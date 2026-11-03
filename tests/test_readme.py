"""The README's setup snippets must work when copied into a new Django project."""
import importlib.util
import os
import re
import textwrap
import types
import warnings
from datetime import timedelta
from pathlib import Path
from unittest import mock, skipUnless

from django.contrib import admin
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import path, reverse

README = Path(__file__).resolve().parent.parent / "README.md"
DOCS_INSTALLED = importlib.util.find_spec("drf_yasg") is not None


def readme_python_block(marker):
    text = README.read_text(encoding="utf-8")
    for block in re.findall(r"```python\n(.*?)```", text, re.S):
        if marker in block:
            return textwrap.dedent(block)
    raise AssertionError(f"no ```python block containing {marker!r} in README.md")


def quick_start_settings():
    namespace = {"INSTALLED_APPS": []}
    exec(readme_python_block("INSTALLED_APPS +="), namespace)
    return namespace


class ReadmeSnippetTests(SimpleTestCase):
    def test_installed_apps_snippet_adds_each_app(self):
        apps = quick_start_settings()["INSTALLED_APPS"]

        for app in (
            "rest_framework",
            "django_simple_third_party_jwt",
            "django_simple_third_party_jwt_dev_dashboard",
        ):
            self.assertIn(app, apps)
        # The pages bring their own styles now.
        self.assertNotIn("bootstrap3", apps)

    def test_settings_snippet_sets_jwt_3rd_prefix(self):
        # django-simple-third-party-jwt's urls.py reads settings.JWT_3RD_PREFIX
        # directly, so the project does not start without it.
        namespace = quick_start_settings()

        self.assertEqual(namespace["JWT_3RD_PREFIX"], "api")
        self.assertEqual(namespace["DEV_DASHBOARD_SETTINGS"]["dashboard_url"], "api/__hidden_dev_dashboard")
        self.assertEqual(namespace["LOGIN_REDIRECT_URL"], "/api/__hidden_dev_dashboard")

    def test_settings_snippet_no_longer_relaxes_security_headers(self):
        # The dashboard pages send what Sign in with Google needs; the project keeps Django's defaults.
        self.assertNotIn("SECURE_", readme_python_block("INSTALLED_APPS +="))

    def test_hand_written_urls_snippet_still_works(self):
        namespace = {"path": path, "urlpatterns": []}
        exec(readme_python_block("TokenObtainPairView.as_view()"), namespace)

        self.assertEqual(len(namespace["urlpatterns"]), 5)

    def test_third_party_snippet_has_placeholders_and_reads_the_secret_from_env(self):
        # Copying the README must never hand out somebody's real OAuth app or secret.
        namespace = {}
        with mock.patch.dict(os.environ, {"SOCIAL_MICROSOFT_CLIENT_SECRET": "from-the-environment"}):
            exec(readme_python_block("SOCIAL_MICROSOFT_CLIENT_SECRET ="), namespace)

        self.assertEqual(namespace["SOCIAL_GOOGLE_CLIENT_ID"], "<your-client-id>.apps.googleusercontent.com")
        self.assertEqual(namespace["SOCIAL_MICROSOFT_CLIENT_ID"], "<your-application-client-id>")
        self.assertEqual(namespace["SOCIAL_MICROSOFT_CLIENT_SECRET"], "from-the-environment")

    def test_api_docs_settings_snippet_turns_both_pages_on(self):
        namespace = {"INSTALLED_APPS": [], "DEV_DASHBOARD_SETTINGS": {}}
        exec(readme_python_block('DEV_DASHBOARD_SETTINGS["swagger_url"]'), namespace)

        self.assertEqual(namespace["INSTALLED_APPS"], ["drf_yasg"])
        self.assertEqual(
            namespace["DEV_DASHBOARD_SETTINGS"],
            {"swagger_url": "api/__hidden_swagger", "redoc_url": "api/__hidden_redoc"},
        )

    @skipUnless(DOCS_INSTALLED, "needs the [docs] extra: pip install -e .[docs]")
    def test_hand_wired_api_docs_snippet_adds_both_pages(self):
        # It follows the hand-written urls.py block, which defines dashboard_urls.
        dashboard_urls = {"swagger_url": "api/__hidden_swagger", "redoc_url": "api/__hidden_redoc"}
        urls_ns = {"path": path, "urlpatterns": [], "dashboard_urls": dashboard_urls}

        with warnings.catch_warnings():
            # drf-yasg and its dependencies warn about their own deprecations on import.
            warnings.simplefilter("ignore", DeprecationWarning)
            exec(readme_python_block("get_schema_view("), urls_ns)

        self.assertEqual(
            [(str(p.pattern), p.name) for p in urls_ns["urlpatterns"]],
            [("api/__hidden_swagger/", "schema-swagger-ui"), ("api/__hidden_redoc/", "schema-redoc")],
        )

    def test_simple_jwt_snippet_sets_token_lifetimes(self):
        namespace = {}
        exec(readme_python_block("SIMPLE_JWT = {"), namespace)

        self.assertEqual(namespace["SIMPLE_JWT"]["ACCESS_TOKEN_LIFETIME"], timedelta(minutes=60))
        self.assertEqual(namespace["SIMPLE_JWT"]["REFRESH_TOKEN_LIFETIME"], timedelta(days=1))


class ReadmeUrlsSnippetTests(TestCase):
    def test_one_line_urls_snippet_serves_the_dashboard_in_a_new_project(self):
        # A urls.py made by `django-admin startproject` imports `admin` and `path` and has the admin.
        namespace = {"admin": admin, "path": path, "urlpatterns": [path("admin/", admin.site.urls)]}
        exec(readme_python_block('all_urls")'), namespace)
        module = types.ModuleType("readme_urls")
        module.urlpatterns = namespace["urlpatterns"]

        with override_settings(ROOT_URLCONF=module):
            self.assertEqual(self.client.get("/api/__hidden_dev_dashboard/").status_code, 200)
            self.assertEqual(reverse("token_get"), "/api/auth/token")
            self.assertEqual(reverse("google-token"), "/api/auth/google/token")
            self.assertEqual(reverse("admin:index"), "/admin/")


class ReadmeImageTests(SimpleTestCase):
    def test_every_screenshot_is_in_the_repo_and_small(self):
        # Images use raw.githubusercontent.com links so they also show on PyPI.
        text = README.read_text(encoding="utf-8")
        prefix = "https://raw.githubusercontent.com/NatLee/django-simple-3rd-party-jwt-dev-dashboard/main/"
        links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text) + re.findall(r'(?:src|srcset)="([^"]+)"', text)
        badges = ("https://img.shields.io/", "https://github.com/NatLee/django-simple-3rd-party-jwt-dev-dashboard/actions/")
        images = [link for link in links if not link.startswith(badges)]

        self.assertGreaterEqual(len(images), 4)
        for link in images:
            self.assertTrue(link.startswith(prefix), link)
            local = README.parent / link[len(prefix):]
            self.assertTrue(local.is_file(), local)
            self.assertLess(local.stat().st_size, 100_000, local)
