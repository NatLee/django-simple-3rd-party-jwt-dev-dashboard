"""Package-level pieces that the views do not exercise: settings defaults, forms, app config."""
import importlib

from django.apps import apps
from django.conf import settings
from django.test import SimpleTestCase

from django_simple_third_party_jwt_dev_dashboard import forms
from django_simple_third_party_jwt_dev_dashboard import settings as dashboard_settings


class DashboardSettingsTests(SimpleTestCase):
    def tearDown(self):
        # Re-read the real test settings so later tests see them again.
        importlib.reload(dashboard_settings)

    def test_project_settings_are_used_as_they_are(self):
        importlib.reload(dashboard_settings)

        self.assertEqual(dashboard_settings.DEV_DASHBOARD_SETTINGS, settings.DEV_DASHBOARD_SETTINGS)
        self.assertEqual(dashboard_settings.JWT_3RD_PREFIX, "api")

    def test_defaults_when_the_project_sets_nothing(self):
        with self.settings():
            del settings.DEV_DASHBOARD_SETTINGS
            del settings.JWT_3RD_PREFIX
            importlib.reload(dashboard_settings)

        self.assertEqual(
            dashboard_settings.DEV_DASHBOARD_SETTINGS,
            {
                "jwt_token_url": "api/auth/token",
                "jwt_refresh_url": "api/auth/token/refresh",
                "jwt_verify_url": "api/auth/token/verify",
                "dashboard_url": "api/__hidden_dev_dashboard",
                "admin_url": "api/__hidden_admin",
                "swagger_url": "api/__hidden_swagger",
                "redoc_url": "api/__hidden_redoc",
            },
        )
        self.assertEqual(dashboard_settings.JWT_3RD_PREFIX, "api")


class FormTests(SimpleTestCase):
    def test_user_form_asks_for_username_and_hidden_password(self):
        form = forms.UserForm()

        self.assertEqual(list(form.fields), ["username", "password"])
        self.assertIn('type="password"', str(form["password"]))

    def test_user_registration_form_asks_for_username_and_hidden_password(self):
        form = forms.UserRegistrationForm()

        self.assertEqual(list(form.fields), ["username", "password"])
        self.assertIn('type="password"', str(form["password"]))


class AppConfigTests(SimpleTestCase):
    def test_app_is_installed_with_its_own_config(self):
        config = apps.get_app_config("django_simple_third_party_jwt_dev_dashboard")

        self.assertEqual(type(config).__name__, "DjangoSimpleThirdPartyJWTDevDashboardConfig")
        self.assertEqual(config.default_auto_field, "django.db.models.BigAutoField")
