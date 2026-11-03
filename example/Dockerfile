# The example project with the dashboard installed from this checkout.
# Run it with `docker compose up --build` in this folder; see compose.yaml.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /src
COPY . .
RUN pip install --no-cache-dir .

WORKDIR /src/example/django_simple_third_party_jwt_dev_dashboard_example
EXPOSE 8000
# createsuperuser reads DJANGO_SUPERUSER_* from compose.yaml; on a restart the user already exists.
CMD ["sh", "-c", "python manage.py migrate --noinput && (python manage.py createsuperuser --noinput || true) && exec python manage.py runserver 0.0.0.0:8000"]
