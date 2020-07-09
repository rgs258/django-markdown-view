import logging

import markdown
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.template import Engine, Template, Context
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from markdown_view.constants import (
    DEFAULT_MARKDOWN_VIEW_LOADERS,
    DEFAULT_MARKDOWN_VIEW_EXTENSIONS, DEFAULT_MARKDOWN_VIEW_TEMPLATE,
    DEFAULT_MARKDOWN_VIEW_USE_REQUEST_CONTEXT, DEFAULT_MARKDOWN_VIEW_EXTRA_CONTEXT,
    DEFAULT_MARKDOWN_VIEW_TEMPLATE_USE_HIGHLIGHT_JS, DEFAULT_MARKDOWN_VIEW_TEMPLATE_USE_TOC,
)

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
            template = Template(
                "{{% load static %}}{}".format(md.convert(template.source))
            )
            render_context_base = {}
            if getattr(
                    settings,
                    "MARKDOWN_VIEW_USE_REQUEST_CONTEXT",
                    DEFAULT_MARKDOWN_VIEW_USE_REQUEST_CONTEXT
            ):
                render_context_base = context
            render_context = Context({
                **render_context_base,
                **(getattr(
                    settings,
                    "MARKDOWN_VIEW_EXTRA_CONTEXT",
                    DEFAULT_MARKDOWN_VIEW_EXTRA_CONTEXT
                ))
            })
            context.update({
                "markdown_content": mark_safe(template.render(render_context)),
                "use_highlight_js": getattr(
                    settings,
                    "MARKDOWN_VIEW_TEMPLATE_USE_HIGHLIGHT_JS",
                    DEFAULT_MARKDOWN_VIEW_TEMPLATE_USE_HIGHLIGHT_JS
                ),
                "use_toc": False,
            })

            if getattr(
                    settings,
                    "MARKDOWN_VIEW_TEMPLATE_USE_TOC",
                    DEFAULT_MARKDOWN_VIEW_TEMPLATE_USE_TOC
            ):
                context.update({
                    "markdown_toc": mark_safe(md.toc),
                    "page_title": mark_safe(md.toc_tokens[0]['name']),
                    "use_toc": True,
                })

        return context

    template_name = getattr(
        settings,
        "MARKDOWN_VIEW_TEMPLATE",
        DEFAULT_MARKDOWN_VIEW_TEMPLATE
    )


class LoggedInMarkdownView(LoginRequiredMixin, MarkdownView):
    pass


class StaffMarkdownView(UserPassesTestMixin, MarkdownView):
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff
