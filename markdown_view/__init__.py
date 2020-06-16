from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from markdown_view import views

SETTINGS_TYPES = {
    "MARKDOWN_VIEW_LOADERS": list,
    "MARKDOWN_VIEW_EXTENSIONS": list,
    "MARKDOWN_VIEW_BASE_DIR": str
}

# Validate settings types.
for variable, instance_type in SETTINGS_TYPES.items():
    if (
        hasattr(settings, variable)
        and not isinstance(getattr(settings, variable), instance_type)
    ):
        raise ImproperlyConfigured(
            "Setting %s is not of type" % variable, instance_type
        )

default_app_config = "markdown_view.apps.MarkdownViewConfig"

MarkdownView = views.MarkdownView
LoggedInMarkdownView = views.LoggedInMarkdownView
StaffMarkdownView = views.StaffMarkdownView
