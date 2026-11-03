"""The README's setup snippets must work when copied into a new Django project."""
import os
import re
import textwrap
import warnings
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.contrib import admin
from django.test import SimpleTestCase
from django.urls import path

README = Path(__file__).resolve().parent.parent / "README.md"


def readme_python_block(marker):
    text = README.read_text(encoding="utf-8")
    for block in re.findall(r"```python\n(.*?)```", text, re.S):
        if marker in block:
            return textwrap.dedent(block)
    raise AssertionError(f"no ```python block containing {marker!r} in README.md")


class ReadmeSnippetTests(SimpleTestCase):
    def test_installed_apps_snippet_adds_each_app(self):
        namespace = {"INSTALLED_APPS": []}
        exec(readme_python_block("INSTALLED_APPS +="), namespace)

        for app in (
            "rest_framework",
            "bootstrap3",
            "django_simple_third_party_jwt",
            "django_simple_third_party_jwt_dev_dashboard",
        ):
            self.assertIn(app, namespace["INSTALLED_APPS"])

    def test_settings_snippet_sets_jwt_3rd_prefix(self):
        # django-simple-third-party-jwt's urls.py reads settings.JWT_3RD_PREFIX
        # directly, so the project does not start without it.
        namespace = {}
        exec(readme_python_block("DEV_DASHBOARD_SETTINGS = {"), namespace)

        self.assertIn("JWT_3RD_PREFIX", namespace)
        self.assertIn("dashboard_url", namespace["DEV_DASHBOARD_SETTINGS"])

    def test_urls_snippet_runs_in_a_new_project_urls_py(self):
        # A urls.py made by `django-admin startproject` only imports `admin` and `path`.
        namespace = {"admin": admin, "path": path, "urlpatterns": []}
        exec(readme_python_block("urlpatterns +="), namespace)

        self.assertEqual(len(namespace["urlpatterns"]), 6)

    def test_third_party_snippet_has_placeholders_and_reads_the_secret_from_env(self):
        # Copying the README must never hand out somebody's real OAuth app or secret.
        namespace = {}
        with mock.patch.dict(os.environ, {"SOCIAL_MICROSOFT_CLIENT_SECRET": "from-the-environment"}):
            exec(readme_python_block("SOCIAL_MICROSOFT_CLIENT_SECRET ="), namespace)

        self.assertEqual(namespace["SOCIAL_GOOGLE_CLIENT_ID"], "<your-client-id>.apps.googleusercontent.com")
        self.assertEqual(namespace["SOCIAL_MICROSOFT_CLIENT_ID"], "<your-application-client-id>")
        self.assertEqual(namespace["SOCIAL_MICROSOFT_CLIENT_SECRET"], "from-the-environment")

    def test_swagger_snippets_add_both_pages(self):
        settings_ns = {"DEV_DASHBOARD_SETTINGS": {}}
        exec(readme_python_block('DEV_DASHBOARD_SETTINGS["swagger_url"]'), settings_ns)
        urls_ns = {"path": path, "urlpatterns": [], "dashboard_urls": settings_ns["DEV_DASHBOARD_SETTINGS"]}

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


class ReadmeImageTests(SimpleTestCase):
    def test_every_screenshot_is_in_the_repo_and_small(self):
        # Images use raw.githubusercontent.com links so they also show on PyPI.
        text = README.read_text(encoding="utf-8")
        prefix = "https://raw.githubusercontent.com/NatLee/django-simple-3rd-party-jwt-dev-dashboard/main/"
        links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
        badges = ("https://img.shields.io/", "https://github.com/NatLee/django-simple-3rd-party-jwt-dev-dashboard/actions/")
        images = [link for link in links if not link.startswith(badges)]

        self.assertTrue(images)
        for link in images:
            self.assertTrue(link.startswith(prefix), link)
            local = README.parent / link[len(prefix):]
            self.assertTrue(local.is_file(), local)
            self.assertLess(local.stat().st_size, 100_000, local)
