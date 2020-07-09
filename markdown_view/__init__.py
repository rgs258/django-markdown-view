from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

SETTINGS_TYPES = {
    "MARKDOWN_VIEW_LOADERS": list,
    "MARKDOWN_VIEW_LOADER_TEMPLATES_DIR": str,
    "MARKDOWN_VIEW_EXTENSIONS": list,
    "MARKDOWN_VIEW_BASE_DIR": str,
    "MARKDOWN_VIEW_TEMPLATE": str,
    "MARKDOWN_VIEW_TEMPLATE_USE_TOC": bool,
    "MARKDOWN_VIEW_TEMPLATE_USE_HIGHLIGHT_JS": bool,
    "MARKDOWN_VIEW_USE_REQUEST_CONTEXT": bool,
    "MARKDOWN_VIEW_EXTRA_CONTEXT": dict
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
