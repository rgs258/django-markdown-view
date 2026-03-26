SECRET_KEY = "test-key"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "markdown_view",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]

ROOT_URLCONF = "markdown_view.tests.urls"
USE_TZ = True
