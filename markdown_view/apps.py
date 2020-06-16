from django.apps import AppConfig
from django.core.checks import register, Tags

from markdown_view.checks import markdown_view_check


class MarkdownViewConfig(AppConfig):
    name = "markdown_view"
    verbose_name = "Serve .md pages as Django templates"

    def ready(self):
        register(markdown_view_check, Tags.security)
