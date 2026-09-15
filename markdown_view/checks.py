from django.conf import settings
from django.core import checks

# Expected type for each optional markdown_view setting. Validated by
# `markdown_view_check()` below (registered as a Django system check in
# `apps.py`), rather than at import time, so `manage.py check` -- and
# `override_settings` in tests -- can exercise this validation directly.
SETTINGS_TYPES = {
    "MARKDOWN_VIEW_LOADERS": list,
    "MARKDOWN_VIEW_LOADER_TEMPLATES_DIR": str,
    "MARKDOWN_VIEW_EXTENSIONS": list,
    "MARKDOWN_VIEW_BASE_DIR": str,
    "MARKDOWN_VIEW_TEMPLATE": str,
    "MARKDOWN_VIEW_TEMPLATE_USE_TOC": bool,
    "MARKDOWN_VIEW_TEMPLATE_USE_HIGHLIGHT_JS": bool,
    "MARKDOWN_VIEW_USE_REQUEST_CONTEXT": bool,
    "MARKDOWN_VIEW_EXTRA_CONTEXT": dict,
    "MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS": bool,
}


def markdown_view_check(app_configs, **kwargs):
    """
    Validate that any of markdown_view's optional settings the project has
    defined are of the expected type.
    """
    errors = []

    for variable, instance_type in SETTINGS_TYPES.items():
        if hasattr(settings, variable) and not isinstance(
            getattr(settings, variable), instance_type
        ):
            errors.append(
                checks.Error(
                    "Setting %s is not of type %s" % (variable, instance_type),
                    hint="Update %s in your settings module to be of type %s."
                    % (variable, instance_type),
                    id="markdown_view.E001",
                )
            )

    return errors
