import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

EXAMPLE = Path(__file__).resolve().parent.parent / "example" / "django_simple_third_party_jwt_dev_dashboard_example"


class ExampleProjectTests(SimpleTestCase):
    def test_example_project_passes_django_checks(self):
        # Run the example's own manage.py with its own settings, not the test settings.
        env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
        result = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=EXAMPLE,
            env=env,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
