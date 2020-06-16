import logging

import markdown
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.template import Engine
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class MarkdownView(TemplateView):
    file_name = None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.file_name:
            engine = Engine(loaders=getattr(
                settings, "MARKDOWN_VIEW_LOADERS", DEFAULT_MARKDOWN_VIEW_LOADERS)
            )
            template = engine.get_template(self.file_name)
            md = markdown.Markdown(extensions=getattr(
                settings,
                "MARKDOWN_VIEW_EXTENSIONS",
                DEFAULT_MARKDOWN_VIEW_EXTENSIONS
            ))
            context.update({
                "markdown_content": mark_safe(md.convert(template.source)),
                "markdown_toc": mark_safe(md.toc),
                "page_title": mark_safe(md.toc_tokens[0]['name']),
            })
        return context

    template_name = "wrds/markdown.html"


class LoggedInMarkdownView(LoginRequiredMixin, MarkdownView):
    pass


class StaffMarkdownView(UserPassesTestMixin, MarkdownView):
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff
