from django.core import checks


def markdown_view_check(app_configs, **kwargs):
    errors = []

    if False:
        errors.extend([checks.Error(
            "Example of a check error",
            hint="Example of a check error hint",
            id="markdown_view.markdown_view_check"
        )])
    return errors
