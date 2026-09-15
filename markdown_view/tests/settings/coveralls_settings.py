"""
Django settings used to run this project's test suite (see ``manage.py`` and
``tox.ini``, which invoke ``manage.py test`` / ``coverage run manage.py
test`` against
``DJANGO_SETTINGS_MODULE=markdown_view.tests.settings.coveralls_settings``).
"""
import os

# The `markdown_view/tests/` directory, used below to locate fixtures.
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The repository root. `markdown_view.loaders.MarkdownLoader` falls back to
# this (via `MarkdownLoader.get_dirs()`) when `MARKDOWN_VIEW_BASE_DIR` isn't
# set, so this is also exercised directly by `test_loaders.py`.
BASE_DIR = os.path.dirname(os.path.dirname(TESTS_DIR))

SECRET_KEY = "not-a-secret-only-used-to-run-tests"
DEBUG = True
ALLOWED_HOSTS = ["*"]

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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

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

# The default `MARKDOWN_VIEW_LOADERS` (`markdown_view.loaders.MarkdownLoader`)
# is used for the vast majority of the suite -- it discovers fixtures under
# `markdown_view/tests/testapp/` via `INSTALLED_APPS`, exactly as it would in
# a real project. `markdown_view.tests.test_registry`'s loader-cache
# invalidation tests override this per-test (via `override_settings`) to
# point at `fixtures/loaders_a`/`fixtures/loaders_b` instead.

AUTH_PASSWORD_VALIDATORS = []

LOGIN_URL = "/accounts/login/"

STATIC_URL = "/static/"

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
