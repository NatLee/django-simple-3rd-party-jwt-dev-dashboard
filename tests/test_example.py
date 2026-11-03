import os
import subprocess
import sys
import warnings
from pathlib import Path

from django.test import SimpleTestCase

EXAMPLE = Path(__file__).resolve().parent.parent / "example" / "django_simple_third_party_jwt_dev_dashboard_example"
EXAMPLE_URLS = EXAMPLE / "django_simple_third_party_jwt_dev_dashboard_example" / "urls.py"
SOCIAL_SETTINGS = ("SOCIAL_GOOGLE_CLIENT_ID", "SOCIAL_MICROSOFT_CLIENT_ID", "SOCIAL_MICROSOFT_CLIENT_SECRET")


def run_example(*args, **extra_env):
    """Run the example's own manage.py with its own settings, not the test settings."""
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE" and k not in SOCIAL_SETTINGS}
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=EXAMPLE,
        env=env,
        capture_output=True,
        text=True,
    )


class ExampleProjectTests(SimpleTestCase):
    def test_example_project_passes_django_checks(self):
        result = run_example("check")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # The dashboard's own startup checks find nothing to complain about either.
        self.assertIn("System check identified no issues", result.stdout, result.stderr)

    def test_example_uses_the_one_line_urls_setup(self):
        text = EXAMPLE_URLS.read_text(encoding="utf-8")

        self.assertIn('include("django_simple_third_party_jwt_dev_dashboard.all_urls")', text)
        self.assertIn('path("admin/", admin.site.urls)', text)

    def test_example_urls_compile_without_warnings(self):
        # Python 3.12+ prints a SyntaxWarning for invalid escapes such as "\." in a
        # normal string, on every manage.py command.
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(EXAMPLE_URLS.read_text(encoding="utf-8"), str(EXAMPLE_URLS), "exec")


class ExampleThirdPartySettingsTests(SimpleTestCase):
    SHOW = (
        "from django.conf import settings; "
        "print([getattr(settings, name, None) == 'from-env-' + name for name in %r])" % (SOCIAL_SETTINGS,)
    )

    def test_values_come_from_the_environment_when_set(self):
        env = {name: "from-env-" + name for name in SOCIAL_SETTINGS}

        result = run_example("shell", "-c", self.SHOW, **env)

        self.assertEqual(result.stdout.strip().splitlines()[-1], "[True, True, True]", result.stderr)

    def test_unset_values_are_left_to_the_base_package(self):
        result = run_example(
            "shell", "-c",
            "from django.conf import settings; print([hasattr(settings, n) for n in %r])" % (SOCIAL_SETTINGS,),
        )

        self.assertEqual(result.stdout.strip().splitlines()[-1], "[False, False, False]", result.stderr)
