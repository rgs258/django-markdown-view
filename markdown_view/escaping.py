"""
Escaping for literal Django template syntax found inside rendered Markdown.

`MarkdownView` re-parses the HTML produced from a `.md` file as a Django
template, so that the `{% static %}` tags `ImageExtension` injects for
image sources (and, when a project opts in via
`MARKDOWN_VIEW_EXTRA_CONTEXT`/`MARKDOWN_VIEW_USE_REQUEST_CONTEXT`, any
`{{ variable }}` references to those context values) actually resolve.

Markdown source files are prose, though, and prose about Django itself
routinely contains literal `{% ... %}`/`{{ ... }}` text that was never
meant to be executed as a template -- e.g. a paragraph explaining how a
template tag works. Left unescaped, that literal text is a genuine
production hazard: an unrecognized `{% ... %}` block raises
`TemplateSyntaxError` (a hard 500 for the whole page), and an unrecognized
`{{ ... }}` variable is silently rendered as an empty string by Django's
default `Context` behavior (silent content loss, with no error at all).

`escape_unsafe_template_syntax()` walks the converted HTML and leaves only
the two genuinely-intended constructs alone -- the exact `{% static '...'
%}` tags `ImageExtension` injects, and `{{ identifier }}` references to a
name actually present in the context the page will render with -- while
converting every other `{% ... %}`/`{{ ... }}` span into inert literal
text, so a documentation author can safely write about template syntax
without needing to know anything about this rendering pipeline.
"""
import re

# The exact shape `ImageExtension.InlineImageProcessor` emits: always
# single-quoted, no filters, no whitespace variation beyond a single space
# after `static`.
_STATIC_TAG_RE = re.compile(r"^\{%\s*static\s+'[^']*'\s*%\}$")

# A bare `{{ identifier }}` reference -- no dotted lookups, no filters. This
# intentionally covers only the simple case `MarkdownView`'s own context-
# variable support is documented/tested against; anything more elaborate
# appearing in a `.md` file is far more likely to be prose describing
# template syntax than a real, intended lookup.
_SIMPLE_VARIABLE_RE = re.compile(r"^\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}$")

# Matches one `{% ... %}` or `{{ ... }}` span at a time, restricted to a
# single line (`.` does not match `\n`) since genuine template tags and
# variable references are not expected to span multiple lines, and
# allowing them to would risk one stray, unmatched delimiter swallowing an
# entire unrelated section of a document into a single "match".
_TEMPLATE_SYNTAX_RE = re.compile(r"(\{%.*?%\})|(\{\{.*?\}\})")


def _escape_braces(text):
    """Render literal ``{``/``}`` characters inert to Django's template lexer."""
    return text.replace("{", "&#123;").replace("}", "&#125;")


def escape_unsafe_template_syntax(html, safe_context_keys=()):
    """
    Escape any ``{% ... %}``/``{{ ... }}`` span in `html` that is not one
    of the two constructs `MarkdownView` genuinely intends to execute,
    rendering it as inert literal text instead.

    :param html: Rendered HTML markup, already converted from Markdown.
    :param safe_context_keys: Top-level variable names that will actually
        be present in the context `html` renders with (e.g. from
        `MARKDOWN_VIEW_EXTRA_CONTEXT` or, when
        `MARKDOWN_VIEW_USE_REQUEST_CONTEXT` is enabled, the view's own
        context). A `{{ name }}` reference to one of these is left alone;
        anything else is treated as literal text.
    :return: `html` with every unsafe template-syntax-shaped span escaped.
    """
    safe_context_keys = set(safe_context_keys)

    def _replace(match):
        block_tag, variable_tag = match.group(1), match.group(2)
        if block_tag is not None:
            if _STATIC_TAG_RE.match(block_tag):
                return block_tag
            return _escape_braces(block_tag)
        variable_match = _SIMPLE_VARIABLE_RE.match(variable_tag)
        if variable_match and variable_match.group(1) in safe_context_keys:
            return variable_tag
        return _escape_braces(variable_tag)

    return _TEMPLATE_SYNTAX_RE.sub(_replace, html)
