"""
Django settings used to run this project's test suite (see ``manage.py`` and
``tox.ini``, which invoke ``manage.py test`` / ``coverage run manage.py
test`` against
``DJANGO_SETTINGS_MODULE=markdown_view.tests.settings.coveralls_settings``).
"""
import os

# The `markdown_view/tests/` directory, used below to locate fixtures.
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "not-a-secret-only-used-to-run-tests"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "markdown_view",
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
        "OPTIONS": {},
    },
]

MARKDOWN_VIEW_LOADERS = [
    (
        "django.template.loaders.filesystem.Loader",
        [os.path.join(TESTS_DIR, "fixtures", "loaders_a")],
    ),
]

USE_TZ = True
