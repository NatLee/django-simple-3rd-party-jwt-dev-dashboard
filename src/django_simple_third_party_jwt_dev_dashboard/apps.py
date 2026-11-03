from django.apps import AppConfig


class DjangoSimpleThirdPartyJWTDevDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_simple_third_party_jwt_dev_dashboard"

    def ready(self) -> None:
        # Registers the startup checks that explain a setup the dashboard cannot work with.
        from django_simple_third_party_jwt_dev_dashboard import checks  # noqa: F401
