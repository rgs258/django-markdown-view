"""Minimal Django settings module for running markdown_view's own test suite.

Referenced from ``manage.py`` via ``DJANGO_SETTINGS_MODULE``, and from
``tox.ini``/CI (``coverage run manage.py test``).
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "not-a-secret-only-used-to-run-tests"

DEBUG = True

ALLOWED_HOSTS = ["testserver"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "markdown_view",
    "markdown_view.tests.testapp",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "markdown_view.tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LOGIN_URL = "/accounts/login/"

STATIC_URL = "/static/"

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
