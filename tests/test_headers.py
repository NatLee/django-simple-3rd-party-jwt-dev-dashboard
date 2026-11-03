"""The dashboard pages send the headers Sign in with Google needs, so the project does not have to."""
from django.test import TestCase, override_settings

DASHBOARD = "/api/__hidden_dev_dashboard/"


class GoogleSignInHeaderTests(TestCase):
    """tests/settings.py keeps Django's default security headers, like a new project."""

    def test_dashboard_pages_send_the_headers_google_sign_in_needs(self):
        for page in (DASHBOARD, DASHBOARD + "login"):
            response = self.client.get(page)

            self.assertEqual(response["Referrer-Policy"], "no-referrer-when-downgrade", page)
            self.assertEqual(response["Cross-Origin-Opener-Policy"], "unsafe-none", page)

    def test_the_rest_of_the_project_keeps_djangos_defaults(self):
        response = self.client.post("/api/auth/token", {"username": "nobody", "password": "x"})

        self.assertEqual(response["Referrer-Policy"], "same-origin")
        self.assertEqual(response["Cross-Origin-Opener-Policy"], "same-origin")

    @override_settings(SECURE_REFERRER_POLICY="no-referrer-when-downgrade", SECURE_CROSS_ORIGIN_OPENER_POLICY=None)
    def test_the_earlier_readme_settings_give_the_same_headers(self):
        response = self.client.get(DASHBOARD)

        self.assertEqual(response["Referrer-Policy"], "no-referrer-when-downgrade")
        self.assertEqual(response["Cross-Origin-Opener-Policy"], "unsafe-none")

    def test_wrong_password_page_also_sends_them(self):
        response = self.client.post(DASHBOARD + "login", {"username": "nobody", "password": "x"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Referrer-Policy"], "no-referrer-when-downgrade")
