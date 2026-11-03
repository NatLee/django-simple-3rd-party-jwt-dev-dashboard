from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from django_simple_third_party_jwt_dev_dashboard import views

DASHBOARD = "/api/__hidden_dev_dashboard/"
LOGIN = DASHBOARD + "login"
LOGOUT = DASHBOARD + "logout"


class DashboardPageTests(TestCase):
    def test_dashboard_renders_for_anonymous_user(self):
        response = self.client.get(DASHBOARD)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dev Dashboard")
        self.assertContains(response, "No session login yet.")

    def test_dashboard_shows_configured_client_ids(self):
        response = self.client.get(DASHBOARD)

        self.assertContains(response, "test-google-client-id.apps.googleusercontent.com")
        self.assertContains(response, "test-microsoft-client-id")

    def test_dashboard_uses_urls_from_dev_dashboard_settings(self):
        response = self.client.get(DASHBOARD)

        # The JavaScript reads the paths from data-* attributes on <body>.
        self.assertContains(response, 'href="/api/__hidden_admin"')
        self.assertContains(response, 'data-dashboard-url="/api/__hidden_dev_dashboard/"')
        self.assertContains(response, 'data-jwt-refresh-url="/api/auth/token/refresh"')
        self.assertContains(response, 'data-jwt-verify-url="/api/auth/token/verify"')

    def test_third_party_login_links_are_the_base_package_routes(self):
        response = self.client.get(DASHBOARD)

        # The Google button's JavaScript posts to data-google-token-url.
        self.assertContains(response, 'data-google-token-url="%s"' % reverse("google-token"))
        self.assertContains(response, 'dd_config("google-token-url")')
        self.assertContains(response, "location.href='%s'" % reverse("microsoft-signin"))


class SessionLoginTests(TestCase):
    def setUp(self):
        User.objects.create_user("alice", password="s3cret-pass")

    def test_login_page_shows_form_and_both_buttons(self):
        response = self.client.get(LOGIN)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, "JWT Login")
        self.assertContains(response, "Session Login")
        self.assertContains(response, 'data-jwt-token-url="/api/auth/token"')

    def test_right_password_starts_a_session(self):
        response = self.client.post(LOGIN, {"username": "alice", "password": "s3cret-pass"})

        self.assertRedirects(response, DASHBOARD)
        self.assertContains(self.client.get(DASHBOARD), "Logged in as <strong>alice</strong>")

    def test_wrong_password_keeps_user_logged_out(self):
        response = self.client.post(LOGIN, {"username": "alice", "password": "wrong"})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_ends_the_session(self):
        self.client.login(username="alice", password="s3cret-pass")

        response = self.client.get(LOGOUT)

        self.assertRedirects(response, DASHBOARD)
        self.assertContains(self.client.get(DASHBOARD), "No session login yet.")


class JWTEndpointTests(TestCase):
    """The dashboard's JavaScript calls these Simple JWT URLs from DEV_DASHBOARD_SETTINGS."""

    def test_token_can_be_obtained_verified_and_refreshed(self):
        User.objects.create_user("alice", password="s3cret-pass")

        response = self.client.post("/api/auth/token", {"username": "alice", "password": "s3cret-pass"})
        self.assertEqual(response.status_code, 200)
        tokens = response.json()

        response = self.client.post("/api/auth/token/verify", {"token": tokens["access"]})
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/api/auth/token/refresh", {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())


class MicrosoftButtonTests(TestCase):
    def test_microsoft_logo_uses_the_original_file_not_a_thumbnail(self):
        # Wikimedia answers HTTP 400 for the 2048px thumbnail the template used,
        # which left a broken image on every page. The original SVG file is served.
        response = self.client.get(DASHBOARD)

        self.assertContains(response, 'src="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg"')
        self.assertNotContains(response, "upload.wikimedia.org/wikipedia/commons/thumb/")


class NavbarTests(TestCase):
    def test_google_sign_in_uses_the_configured_client_id(self):
        response = self.client.get(DASHBOARD)

        self.assertContains(
            response,
            '<meta name="google-signin-client_id" content="test-google-client-id.apps.googleusercontent.com">',
        )
        self.assertContains(response, 'data-client_id="test-google-client-id.apps.googleusercontent.com"')

    def test_anonymous_user_gets_login_but_no_session_logout(self):
        response = self.client.get(DASHBOARD)

        self.assertContains(response, 'href="%s"' % LOGIN)
        self.assertContains(response, "JWT Logout")
        self.assertNotContains(response, "Session Logout")

    def test_logged_in_user_is_greeted_and_can_end_the_session(self):
        User.objects.create_user("alice", password="s3cret-pass")
        self.client.login(username="alice", password="s3cret-pass")

        response = self.client.get(DASHBOARD)

        self.assertContains(response, "Hello alice")
        self.assertContains(response, 'href="/api/__hidden_dev_dashboard/logout"')

    def test_swagger_and_redoc_links_are_hidden_unless_configured(self):
        # tests/settings.py leaves swagger_url and redoc_url out, like the README.
        response = self.client.get(DASHBOARD)

        self.assertNotContains(response, "Swagger")
        self.assertNotContains(response, "Redoc")


class LoginEdgeCaseTests(TestCase):
    def setUp(self):
        User.objects.create_user("alice", password="s3cret-pass")

    def test_wrong_password_shows_the_form_error(self):
        response = self.client.post(LOGIN, {"username": "alice", "password": "wrong"})

        self.assertContains(response, "Please enter a correct username and password")

    def test_login_works_without_a_csrf_token(self):
        # The view is csrf_exempt, as it has always been.
        client = Client(enforce_csrf_checks=True)

        response = client.post(LOGIN, {"username": "alice", "password": "s3cret-pass"})

        self.assertRedirects(response, DASHBOARD)

    def test_logout_sends_anonymous_users_to_the_login_url(self):
        response = self.client.get(LOGOUT)

        self.assertRedirects(
            response,
            "%s?next=%s" % (settings.LOGIN_URL, LOGOUT),
            fetch_redirect_response=False,
        )
