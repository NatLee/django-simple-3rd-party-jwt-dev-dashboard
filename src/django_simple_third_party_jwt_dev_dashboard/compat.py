"""Everything kept only so code written for 0.2.x keeps working, listed in one place.

Nothing in the dashboard itself uses these. They can all go in the next major release (1.0).

- ``forms.UserRegistrationForm`` and ``forms.UserForm``: the login has always used Django's
  AuthenticationForm; these two were never wired to a page. forms.py holds nothing else.
- ``settings.JWT_3RD_PREFIX``: defined below and re-exported by settings.py.
- The ``third_party_jwt_url`` template variable: see ``legacy_context()``.

This module stays light on purpose: settings.py imports it, and that happens at startup.
"""
from typing import Any, Dict

from django.conf import settings

# A copy of django-simple-third-party-jwt's own setting, with "api" (not its "") as the default.
# The pages find that package's routes by URL name instead.
JWT_3RD_PREFIX = getattr(settings, "JWT_3RD_PREFIX", "api")


def legacy_context() -> Dict[str, Any]:
    """Template variables the dashboard's own templates no longer use, for overriding templates."""
    from django_simple_third_party_jwt import settings as jwt_settings

    return {
        # The base package's URL prefix; base.html links to its routes by name instead.
        "third_party_jwt_url": jwt_settings.JWT_3RD_PREFIX,
    }
