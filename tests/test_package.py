"""Package-level pieces that the views do not exercise: settings defaults, forms, app config."""
import importlib
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django import forms as django_forms
from django.test import SimpleTestCase

from django_simple_third_party_jwt_dev_dashboard import compat, forms, views
from django_simple_third_party_jwt_dev_dashboard import settings as dashboard_settings


class DashboardSettingsTests(SimpleTestCase):
    def tearDown(self):
        # Re-read the real test settings so later tests see them again.
        importlib.reload(compat)
        importlib.reload(dashboard_settings)

    def test_project_settings_are_used_as_they_are(self):
        importlib.reload(dashboard_settings)

        self.assertEqual(dashboard_settings.DEV_DASHBOARD_SETTINGS, settings.DEV_DASHBOARD_SETTINGS)
        self.assertEqual(dashboard_settings.JWT_3RD_PREFIX, "api")

    def test_defaults_when_the_project_sets_nothing(self):
        with self.settings():
            del settings.DEV_DASHBOARD_SETTINGS
            del settings.JWT_3RD_PREFIX
            importlib.reload(compat)
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


class CompatTests(SimpleTestCase):
    """The 0.2.x leftovers listed in compat.py stay where old code looks for them."""

    def test_old_import_paths_still_work(self):
        self.assertIs(dashboard_settings.JWT_3RD_PREFIX, compat.JWT_3RD_PREFIX)
        self.assertTrue(issubclass(forms.UserForm, django_forms.ModelForm))
        self.assertTrue(issubclass(forms.UserRegistrationForm, django_forms.ModelForm))

    def test_old_template_variable_is_still_passed(self):
        self.assertEqual(views.dev_dashboard_setting["third_party_jwt_url"], "api")

    def test_the_dashboard_itself_does_not_use_them(self):
        package = Path(views.__file__).resolve().parent
        templates = "".join(p.read_text("utf-8") for p in (package / "templates").rglob("*") if p.is_file())

        self.assertNotIn("third_party_jwt_url", templates)
        for module in ("views.py", "all_urls.py", "checks.py", "urls.py"):
            source = (package / module).read_text("utf-8")
            self.assertNotRegex(source, r"import .*JWT_3RD_PREFIX|settings\.JWT_3RD_PREFIX", module)
            self.assertNotIn("UserForm", source, module)


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
