"""The README's setup snippets must work when copied into a new Django project."""
import re
import textwrap
from pathlib import Path

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
