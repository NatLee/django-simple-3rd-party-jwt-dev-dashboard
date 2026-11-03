"""The Swagger and Redoc pages are the optional [docs] extra; navbar links show only for served pages."""
import importlib
import importlib.util
import types
from importlib.metadata import requires
from unittest import mock, skipUnless

from django.http import HttpResponse
from django.test import SimpleTestCase, TestCase, modify_settings, override_settings
from django.urls import include, path

from django_simple_third_party_jwt_dev_dashboard import all_urls, views
from django_simple_third_party_jwt_dev_dashboard import settings as dashboard_settings

DASHBOARD = "/api/__hidden_dev_dashboard/"
# The paths the README's API docs section uses (and the defaults when DEV_DASHBOARD_SETTINGS is unset).
DOCS_URLS = {"swagger_url": "api/__hidden_swagger", "redoc_url": "api/__hidden_redoc"}
DOCS_INSTALLED = importlib.util.find_spec("drf_yasg") is not None


def urlconf(*patterns):
    module = types.ModuleType("made_up_urls")
    module.urlpatterns = list(patterns)
    return module


def all_urls_with(settings_dict):
    """all_urls as it is built for these DEV_DASHBOARD_SETTINGS (reloaded back in tearDown)."""
    with mock.patch.object(dashboard_settings, "DEV_DASHBOARD_SETTINGS", settings_dict):
        return importlib.reload(all_urls)


class DependencyTests(SimpleTestCase):
    def test_drf_yasg_comes_only_with_the_docs_extra(self):
        drf_yasg = [r for r in requires("django-simple-third-party-jwt-dev-dashboard") if r.lower().startswith("drf-yasg")]

        self.assertEqual(len(drf_yasg), 1, drf_yasg)
        self.assertIn('extra == "docs"', drf_yasg[0])


class LinkVisibilityTests(TestCase):
    """tests/urls.py serves the admin but no API docs, like a project without the [docs] extra."""

    def test_links_to_pages_nobody_serves_are_hidden(self):
        with mock.patch.dict(views.dev_dashboard_setting, DOCS_URLS):
            response = self.client.get(DASHBOARD)

        self.assertNotContains(response, ">Swagger<")
        self.assertNotContains(response, ">Redoc<")
        self.assertEqual(response.context["swagger_url"], "")

    def test_links_show_while_their_pages_are_served(self):
        page = path("", lambda request: HttpResponse("docs"))
        served = urlconf(
            path("", include("tests.urls")),
            path(DOCS_URLS["swagger_url"] + "/", include([page])),
            path(DOCS_URLS["redoc_url"] + "/", include([page])),
        )
        with mock.patch.dict(views.dev_dashboard_setting, DOCS_URLS), override_settings(ROOT_URLCONF=served):
            response = self.client.get(DASHBOARD)

        self.assertContains(response, 'href="/api/__hidden_swagger"')
        self.assertContains(response, 'href="/api/__hidden_redoc"')

    def test_admin_link_follows_the_admin(self):
        # The admin is mounted at "api/__hidden_admin/"; the link has no slash (APPEND_SLASH redirects).
        self.assertContains(self.client.get(DASHBOARD), 'href="/api/__hidden_admin"')

        without_admin = urlconf(
            path("api/__hidden_dev_dashboard/", include("django_simple_third_party_jwt_dev_dashboard.urls")),
            path("", include("django_simple_third_party_jwt.urls")),
        )
        with override_settings(ROOT_URLCONF=without_admin):
            self.assertNotContains(self.client.get(DASHBOARD), ">Admin<")


class WithoutDrfYasgTests(SimpleTestCase):
    def tearDown(self):
        importlib.reload(all_urls)

    def test_all_urls_serves_no_docs_unless_drf_yasg_is_an_installed_app(self):
        # tests/settings.py does not list "drf_yasg", whether or not the package is installed.
        module = all_urls_with({**dashboard_settings.DEV_DASHBOARD_SETTINGS, **DOCS_URLS})

        names = [getattr(p, "name", None) for p in module.urlpatterns]
        self.assertNotIn("schema-swagger-ui", names)
        self.assertNotIn("schema-redoc", names)


@skipUnless(DOCS_INSTALLED, "needs the [docs] extra: pip install -e .[docs]")
@modify_settings(INSTALLED_APPS={"append": "drf_yasg"})
@override_settings(SWAGGER_USE_COMPAT_RENDERERS=False)
class WithDrfYasgTests(TestCase):
    def setUp(self):
        module = all_urls_with({**dashboard_settings.DEV_DASHBOARD_SETTINGS, **DOCS_URLS})
        self.addCleanup(importlib.reload, all_urls)
        for context in (
            override_settings(ROOT_URLCONF=urlconf(path("", include(module.urlpatterns)))),
            mock.patch.dict(views.dev_dashboard_setting, DOCS_URLS),
        ):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)

    def test_swagger_and_redoc_pages_are_served(self):
        for key in DOCS_URLS:
            response = self.client.get("/%s/" % DOCS_URLS[key])

            self.assertEqual(response.status_code, 200, key)

    def test_the_schema_covers_the_jwt_endpoints(self):
        response = self.client.get("/%s/?format=openapi" % DOCS_URLS["swagger_url"])

        self.assertEqual(response.status_code, 200)
        schema = response.json()
        # Swagger 2.0 lists paths relative to the common basePath.
        paths = {schema["basePath"].rstrip("/") + p for p in schema["paths"]}
        self.assertIn("/api/auth/token", paths)
        self.assertIn("/api/auth/google/token", paths)

    def test_the_navbar_links_to_both(self):
        response = self.client.get(DASHBOARD)

        self.assertContains(response, 'href="/api/__hidden_swagger"')
        self.assertContains(response, 'href="/api/__hidden_redoc"')
