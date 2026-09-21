"""
Locate and read a ``markdown_view`` ``file_name`` value's underlying
source file without compiling its raw, pre-Markdown-conversion contents
as a Django template.

Both `MarkdownView` and `registry.py` need to resolve a `file_name` (e.g.
``"users/README.md"``) to an actual file on disk, using whatever loaders
`MARKDOWN_VIEW_LOADERS` configures. The obvious way to do that with
Django's own `Engine`/`Loader` API is `engine.get_template(file_name)` --
but `Loader.get_template()` doesn't just locate the file: it also
constructs a `django.template.base.Template` from its *raw* contents,
which eagerly compiles and validates that source as Django template
syntax immediately, before any Markdown conversion has happened. A `.md`
file whose raw text contains literal template-tag-shaped syntax anywhere
at all -- inside a fenced code block documenting Django itself, for
instance, or in an inline-code span -- would then raise
`TemplateSyntaxError` merely from being *loaded*, well before
`MarkdownView` gets a chance to convert it to HTML, and therefore before
`escaping.escape_unsafe_template_syntax()` (which only ever sees the
already-converted HTML) gets any chance to make that literal syntax safe.

`load_markdown_source()` instead walks the engine's configured loaders and
origins directly, reading each candidate file's raw contents (via each
loader's own `get_contents()`, the same plain, uncompiled read
`Loader.get_template()` itself uses before wrapping the result in a
`Template`) without ever constructing a `Template` from them.
"""
import os

from django.template import TemplateDoesNotExist


def load_markdown_source(file_name, engine):
    """
    Resolve `file_name` to its underlying source file using `engine`'s
    configured template loaders, and return its raw text -- without
    compiling that text as a Django template.

    :param file_name: A `file_name` value, as passed to
        `MarkdownView.as_view(file_name=...)`.
    :param engine: The `django.template.Engine` whose loaders should be
        used to resolve `file_name`.
    :return: A `(source_text, source_path)` tuple, where `source_path` is
        the absolute, normalized filesystem path the source was read from.
    :raises TemplateDoesNotExist: If no configured loader can locate
        `file_name`.
    """
    tried = []
    for loader in engine.template_loaders:
        for origin in loader.get_template_sources(file_name):
            try:
                contents = loader.get_contents(origin)
            except TemplateDoesNotExist:
                tried.append((origin, "Source does not exist"))
                continue
            return contents, os.path.normpath(origin.name)
    raise TemplateDoesNotExist(file_name, tried=tried)
