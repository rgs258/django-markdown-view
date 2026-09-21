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
    DEFAULT_MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS,
    DEFAULT_MARKDOWN_VIEW_ESCAPE_UNSAFE_TEMPLATE_SYNTAX,
)
from markdown_view.escaping import escape_unsafe_template_syntax
from markdown_view.loading import load_markdown_source
from markdown_view.registry import rewrite_markdown_links

logger = logging.getLogger(__name__)


class MarkdownView(TemplateView):
    file_name = None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.file_name:
            engine = Engine(loaders=getattr(
                settings, "MARKDOWN_VIEW_LOADERS", DEFAULT_MARKDOWN_VIEW_LOADERS)
            )
            # Deliberately not `engine.get_template(...)`: that constructs a
            # `Template` from the file's *raw*, pre-Markdown-conversion
            # contents, which eagerly compiles/validates that raw text as
            # Django template syntax -- a `.md` file whose raw source
            # contains literal template-tag-shaped text anywhere (e.g. a
            # fenced code block documenting Django itself) would then raise
            # `TemplateSyntaxError` merely from being loaded, before
            # Markdown conversion or `escape_unsafe_template_syntax()`
            # below ever run. `load_markdown_source()` reads the same file
            # without compiling it as a template.
            source_text, source_path = load_markdown_source(self.file_name, engine)
            md = markdown.Markdown(extensions=getattr(
                settings,
                "MARKDOWN_VIEW_EXTENSIONS",
                DEFAULT_MARKDOWN_VIEW_EXTENSIONS
            ))
            converted_html = md.convert(source_text)
            if getattr(
                    settings,
                    "MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS",
                    DEFAULT_MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS
            ):
                # Rewrite relative links to other .md files (e.g.
                # `[See also](../README-cron.md)`) to the actual routed URL
                # of the MarkdownView serving that file, if one is
                # registered -- otherwise the raw relative link can't
                # resolve, since this page is served at its own URL, not
                # at the source file's location on disk.
                converted_html = rewrite_markdown_links(converted_html, source_path)

            render_context_base = {}
            if getattr(
                    settings,
                    "MARKDOWN_VIEW_USE_REQUEST_CONTEXT",
                    DEFAULT_MARKDOWN_VIEW_USE_REQUEST_CONTEXT
            ):
                render_context_base = context
            extra_context = getattr(
                settings,
                "MARKDOWN_VIEW_EXTRA_CONTEXT",
                DEFAULT_MARKDOWN_VIEW_EXTRA_CONTEXT
            )

            if getattr(
                    settings,
                    "MARKDOWN_VIEW_ESCAPE_UNSAFE_TEMPLATE_SYNTAX",
                    DEFAULT_MARKDOWN_VIEW_ESCAPE_UNSAFE_TEMPLATE_SYNTAX
            ):
                # Markdown source files are prose, and prose about Django
                # itself routinely contains literal `{% ... %}`/`{{ ... }}`
                # text that was never meant to be executed as a template.
                # Render everything except the `{% static %}` tags
                # `ImageExtension` injects, and `{{ name }}` references to
                # a key that will actually be present in the context below,
                # as inert literal text instead -- otherwise an
                # unrecognized block tag raises `TemplateSyntaxError` (a
                # hard 500) and an unrecognized variable silently renders
                # as an empty string (silent content loss).
                converted_html = escape_unsafe_template_syntax(
                    converted_html,
                    safe_context_keys={
                        *render_context_base.keys(), *extra_context.keys()
                    },
                )

            template = Template(
                "{{% load static %}}{}".format(converted_html)
            )
            render_context = Context({
                **render_context_base,
                **extra_context,
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
                toc_context = {
                    "markdown_toc": mark_safe(md.toc),
                    "use_toc": True,
                }
                toc_tokens = getattr(md, "toc_tokens", []) or []
                if toc_tokens and "name" in toc_tokens[0]:
                    toc_context["page_title"] = mark_safe(toc_tokens[0]["name"])
                context.update(toc_context)

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
