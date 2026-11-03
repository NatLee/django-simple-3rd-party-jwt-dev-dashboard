"""What the redesigned pages promise: states, assets, and the parts that overriding templates rely on."""
import re
import tempfile
import types
from importlib.metadata import requires
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.template import engines
from django.test import RequestFactory, TestCase, override_settings
from django.urls import include, path

from django_simple_third_party_jwt_dev_dashboard import __version__, views

DASHBOARD = "/api/__hidden_dev_dashboard/"
LOGIN = DASHBOARD + "login"
PACKAGE = Path(views.__file__).resolve().parent  # the installed copy (site-packages under tox)
TEMPLATES = PACKAGE / "templates" / views.TEMPLATE_DIR


class StateTests(TestCase):
    def test_anonymous_visitor_sees_no_jwt_and_no_session(self):
        response = self.client.get(DASHBOARD)

        self.assertContains(response, 'data-jwt-state="none"')
        self.assertContains(response, "No JWT in this browser yet.")
        self.assertContains(response, 'data-session-state="none"')
        self.assertContains(response, "No session")

    def test_session_login_shows_who_and_their_role(self):
        User.objects.create_superuser("root", password="s3cret-pass")
        self.client.login(username="root", password="s3cret-pass")

        response = self.client.get(DASHBOARD)

        self.assertContains(response, 'data-session-state="in"')
        self.assertContains(response, "Logged in as <strong>root</strong>")
        self.assertContains(response, '<span class="dd-badge">superuser</span>')
        self.assertContains(response, '<span class="dd-avatar" aria-hidden="true">R</span>')

    def test_wrong_password_is_shown_on_the_login_page(self):
        response = self.client.post(LOGIN, {"username": "nobody", "password": "wrong"})

        self.assertContains(response, '<div class="dd-alert dd-alert--error" role="alert">')
        self.assertContains(response, "Please enter a correct username and password")
        # The username stays in the form.
        self.assertContains(response, 'value="nobody"')

    def test_debug_tag_follows_the_setting(self):
        self.assertContains(self.client.get(DASHBOARD), "DEBUG off")
        with mock.patch.dict(views.dev_dashboard_setting, {"debug": True}):
            response = self.client.get(DASHBOARD)

        self.assertContains(response, 'class="dd-tag dd-tag--ok"')
        self.assertNotContains(response, "DEBUG off")

    def test_footer_shows_the_package_version(self):
        self.assertContains(self.client.get(DASHBOARD), "django-simple-third-party-jwt-dev-dashboard " + __version__)

    def test_current_page_is_marked_in_the_navbar(self):
        self.assertContains(self.client.get(LOGIN), 'href="%s" aria-current="page"' % LOGIN)


class LinkTests(TestCase):
    """Links come from the URLconf by name, not from a copy of its layout."""

    def urlconf(self, *patterns):
        module = types.ModuleType("made_up_urls")
        module.urlpatterns = list(patterns)
        return module

    def test_links_follow_the_routes_wherever_they_are_mounted(self):
        moved = self.urlconf(
            path("dev/", include("django_simple_third_party_jwt_dev_dashboard.urls")),
            path("sso/", include("django_simple_third_party_jwt.urls")),
        )
        with override_settings(ROOT_URLCONF=moved):
            User.objects.create_user("alice", password="s3cret-pass")
            self.client.login(username="alice", password="s3cret-pass")
            html = self.client.get("/dev/").content.decode()

        self.assertIn('data-dashboard-url="/dev/"', html)
        self.assertIn('href="/dev/logout"', html)
        self.assertIn('data-google-token-url="/sso/api/auth/google/token"', html)
        self.assertIn("location.href='/sso/api/auth/microsoft/signin'", html)
        self.assertIn("<code>/sso/api/auth/google/token</code>", html)

    def test_without_the_base_package_routes_the_buttons_are_replaced_by_a_note(self):
        alone = self.urlconf(path("dev/", include("django_simple_third_party_jwt_dev_dashboard.urls")))
        with override_settings(ROOT_URLCONF=alone):
            response = self.client.get("/dev/")

        self.assertContains(response, "Not available: this project does not include")
        self.assertNotContains(response, 'id="microsoft-login-button"')
        self.assertNotContains(response, 'class="g_id_signin"')


class SignInSetupTests(TestCase):
    """A sign-in without a client ID (no Microsoft demo app after django-simple-third-party-jwt 0.4.0)."""

    def not_set_up(self, key):
        sign_ins = {**views.SIGN_INS, key: views.SignIn(views.SIGN_INS[key].label, None)}
        return mock.patch.dict(views.dev_dashboard_setting, {"sign_ins": sign_ins, "social_%s_client_id" % key: None})

    def test_configured_means_the_setting_has_a_value(self):
        self.assertTrue(views.SignIn("Microsoft", "an-id").configured)
        self.assertFalse(views.SignIn("Microsoft", None).configured)
        self.assertFalse(views.SignIn("Microsoft", "").configured)

    def test_the_test_settings_set_up_both(self):
        response = self.client.get(DASHBOARD)

        self.assertContains(response, 'id="microsoft-login-button"')
        self.assertContains(response, 'class="g_id_signin"')
        self.assertNotContains(response, "is not set up")

    def test_microsoft_without_a_client_id(self):
        with self.not_set_up("microsoft"):
            response = self.client.get(DASHBOARD)

        self.assertNotContains(response, "None")
        self.assertNotContains(response, 'id="microsoft-login-button"')
        self.assertContains(response, "Microsoft sign-in is not set up")
        self.assertContains(response, '<span class="dd-muted">Not set up</span>')
        self.assertContains(response, 'class="g_id_signin"')  # Google is untouched

    def test_google_without_a_client_id(self):
        with self.not_set_up("google"):
            response = self.client.get(DASHBOARD)

        self.assertNotContains(response, "None")
        self.assertNotContains(response, 'class="g_id_signin"')
        self.assertNotContains(response, 'name="google-signin-client_id"')
        self.assertContains(response, "Google sign-in is not set up")
        self.assertContains(response, 'id="microsoft-login-button"')


class TokenStorageTests(TestCase):
    """The tokens go where django-simple-third-party-jwt's Microsoft login puts them."""

    def test_storage_keys_come_from_the_base_package(self):
        from django_simple_third_party_jwt import settings as jwt_settings

        self.assertEqual(views.dev_dashboard_setting["access_token_key"], jwt_settings.MICROSOFT_JWT_REDIRECT_ACCESS_TOKEN_KEY)
        self.assertEqual(views.dev_dashboard_setting["refresh_token_key"], jwt_settings.MICROSOFT_JWT_REDIRECT_REFRESH_TOKEN_KEY)

    def test_pages_pass_the_keys_to_the_script(self):
        keys = {"access_token_key": "my_access", "refresh_token_key": "my_refresh"}
        with mock.patch.dict(views.dev_dashboard_setting, keys):
            response = self.client.get(DASHBOARD)

        self.assertContains(response, 'data-access-token-key="my_access"')
        self.assertContains(response, 'data-refresh-token-key="my_refresh"')

    def test_script_has_no_storage_keys_of_its_own(self):
        script = (TEMPLATES / "dashboard.js").read_text("utf-8")

        self.assertNotIn('"access_token"', script)
        self.assertNotIn('"refresh_token"', script)
        # Only the dd_tokens object reads or writes localStorage.
        start = script.index("var dd_tokens")
        outside = script[:start] + script[script.index("\n};\n", start):]
        self.assertNotIn("localStorage.", outside)


class LoginFormTests(TestCase):
    def test_session_login_is_a_plain_form_post_to_the_login_view(self):
        # It works without JavaScript; only JWT Login needs it.
        response = self.client.get(LOGIN)

        self.assertContains(response, '<form id="login-form" class="dd-form" autocomplete="off" method="POST" action="%s">' % LOGIN)
        self.assertContains(response, 'name="action" value="jwt"')
        self.assertContains(response, 'name="action" value="session"')
        self.assertContains(response, 'bind_login_form(document.getElementById("login-form"))')

    def test_session_button_value_does_not_bother_the_view(self):
        User.objects.create_user("alice", password="s3cret-pass")

        response = self.client.post(LOGIN, {"username": "alice", "password": "s3cret-pass", "action": "session"})

        self.assertRedirects(response, DASHBOARD)


class AssetTests(TestCase):
    def test_styles_and_scripts_are_inline(self):
        html = self.client.get(DASHBOARD).content.decode()

        self.assertIn("@media (prefers-color-scheme: dark)", html)
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', html)
        self.assertIn("function refresh_stored_token()", html)
        self.assertNotIn("<link", html)  # no stylesheet from a CDN

    def test_the_only_external_script_is_googles_sign_in(self):
        # Google serves one moving version of it, so it cannot carry an integrity hash.
        for page in (DASHBOARD, LOGIN):
            html = self.client.get(page).content.decode()

            self.assertEqual(re.findall(r'<script src="([^"]+)"', html), ["https://accounts.google.com/gsi/client"])

    def test_needs_neither_bootstrap3_nor_jquery(self):
        # Dropped in 0.3.0 (user decision): the package does not depend on django-bootstrap3,
        # tests/settings.py does not install it, and no page loads jQuery.
        dependencies = [r.lower() for r in requires("django-simple-third-party-jwt-dev-dashboard")]

        self.assertFalse([r for r in dependencies if r.startswith("django-bootstrap3")])
        for template in (p for p in (PACKAGE / "templates").rglob("*") if p.is_file()):
            source = template.read_text("utf-8")

            self.assertNotIn("bootstrap", source.lower(), template.name)
            self.assertIsNone(re.search(r"\$\(|\bjQuery\b", source), template.name)
        # test_the_only_external_script_is_googles_sign_in covers the jQuery <script> itself.

    def test_page_templates_leave_colours_to_the_stylesheet(self):
        # Colours live in dashboard.css as variables, so overriding them restyles everything.
        for name in ("base.html", "dashboard.html", "login.html"):
            source = (TEMPLATES / name).read_text("utf-8")

            self.assertNotIn('style="', source, name)

    def test_included_files_have_no_template_tags(self):
        # base.html includes them as templates; a stray "{%" would break every page.
        for name in ("dashboard.css", "dashboard.js", "microsoft-logo.svg"):
            text = (TEMPLATES / name).read_text("utf-8")
            self.assertIsNone(re.search(r"\{[{%#]", text), name)


class TemplateNamespaceTests(TestCase):
    """Since 0.3.0 the pages are django_simple_third_party_jwt_dev_dashboard/<name>.html."""

    def project_templates(self, files):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        for name, text in files.items():
            Path(folder.name, name).parent.mkdir(parents=True, exist_ok=True)
            Path(folder.name, name).write_text(text, encoding="utf-8")
        return override_settings(TEMPLATES=[dict(settings.TEMPLATES[0], DIRS=[folder.name])])

    def test_a_projects_own_base_html_no_longer_takes_over(self):
        # Before 0.3.0 a project-level templates/base.html replaced the dashboard's.
        with self.project_templates({"base.html": "project base", "dashboard.html": "project page"}):
            response = self.client.get(DASHBOARD)

        self.assertContains(response, 'id="jwt-card"')
        self.assertNotContains(response, "project base")
        self.assertNotContains(response, "project page")

    def test_a_project_overrides_a_page_under_the_namespace(self):
        page = (
            '{% extends "django_simple_third_party_jwt_dev_dashboard/base.html" %}'
            "{% block content %}<p>my dashboard</p>{% endblock %}"
        )
        with self.project_templates({"django_simple_third_party_jwt_dev_dashboard/dashboard.html": page}):
            response = self.client.get(DASHBOARD)

        self.assertContains(response, "<p>my dashboard</p>")
        self.assertContains(response, 'id="microsoft-login-button"')


class OverrideContractTests(TestCase):
    """Projects override these templates; names, blocks, ids and functions must stay."""

    def render(self, source, path=DASHBOARD):
        request = RequestFactory().get(path)
        request.user = mock.Mock(is_authenticated=False)
        return engines["django"].from_string(source).render(views.dev_dashboard_setting, request)

    def test_blocks_of_base_html(self):
        html = self.render(
            '{% extends "django_simple_third_party_jwt_dev_dashboard/base.html" %}{% block title %}T1{% endblock %}'
            "{% block extra_head %}<style>.mine{}</style>{% endblock %}"
            "{% block content %}<p>my page</p>{% endblock %}"
            "{% block aside %}{{ block.super }}<p>my aside</p>{% endblock %}"
        )

        self.assertIn("<title>T1</title>", html)
        self.assertIn("<style>.mine{}</style>\n</head>", html)
        self.assertIn("<p>my page</p>", html)
        self.assertIn("<p>my aside</p>", html)
        self.assertIn('id="microsoft-login-button"', html)  # block.super keeps the third-party card

    def test_global_functions_keep_their_names(self):
        html = self.client.get(DASHBOARD).content.decode()

        for signature in (
            "function show_login_error(xhr)",
            "function show_verified_token(access_token, message)",
            "function get_jwt_using_google_credential(response)",
            "function logout()",
        ):
            self.assertIn(signature, html)
        self.assertIn('data-callback="get_jwt_using_google_credential"', html)
        self.assertIn('id="token"', html)
        self.assertIn('id="result"', html)

    def test_context_variables_are_unchanged(self):
        response = self.client.get(DASHBOARD)

        for name in (
            "social_google_client_id", "social_microsoft_client_id", "third_party_jwt_url",
            "jwt_token_url", "jwt_refresh_url", "jwt_verify_url", "dashboard_url",
            "admin_url", "swagger_url", "redoc_url", "debug",
        ):
            self.assertIn(name, response.context, name)
        self.assertIn("form", self.client.get(LOGIN).context)
