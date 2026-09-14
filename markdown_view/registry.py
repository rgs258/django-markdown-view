"""
Registry mapping ``MarkdownView`` (and subclass) ``file_name`` values to the
concrete URLs that serve them.

Markdown source files commonly link to other markdown files using plain,
filesystem-relative links (e.g. ``[See also](../README-cron.md)``), exactly
as they would on GitHub or in a local editor. When such a file is rendered
as an HTML page instead of viewed as a raw file, that relative link no
longer resolves to anything meaningful in the browser -- the rendered page
lives at whatever URL its own view was routed to, not at the file's
location on disk.

This module lets ``MarkdownView`` automatically discover, for any given
target ``.md`` file, whether some URL pattern in the project serves that
file via a ``MarkdownView`` (or subclass), and if so, resolve to that URL
instead of leaving the raw relative path in place.

This is intentionally best-effort: routes behind a required URL argument,
or wrapped by a decorator that doesn't preserve the underlying view's
``view_class``/``view_initkwargs`` attributes, are silently skipped. A link
that can't be resolved to a known route is left exactly as markdown would
otherwise have rendered it, so nothing breaks if a target file simply isn't
routed anywhere.
"""
import logging
import os
import re

from django.conf import settings
from django.template import Engine
from django.urls import NoReverseMatch, URLResolver, get_resolver, reverse

from markdown_view.constants import DEFAULT_MARKDOWN_VIEW_LOADERS

logger = logging.getLogger(__name__)

# Lazily constructed, since it depends on settings being configured.
_engine = None

# Cached {id(resolver): {absolute file path: URL}} registries. Keyed by the
# resolver's identity (Django itself caches `get_resolver()` per urlconf, so
# this naturally rebuilds if `ROOT_URLCONF`/the active urlconf ever changes,
# e.g. under `override_settings` in tests).
_registry_cache = {}


def _get_engine():
    """
    Return a lazily constructed `Engine` configured with the same template
    loaders `MarkdownView` itself uses, so relative `file_name` values
    resolve identically here and at render time.
    """
    global _engine
    if _engine is None:
        _engine = Engine(
            loaders=getattr(
                settings, "MARKDOWN_VIEW_LOADERS", DEFAULT_MARKDOWN_VIEW_LOADERS
            )
        )
    return _engine


def resolve_markdown_source_path(file_name):
    """
    Resolve a markdown_view `file_name` to the absolute filesystem path of
    its underlying source file, using the same template-loader resolution
    `MarkdownView` uses to actually load and render it.

    :param file_name: A `file_name` value, as passed to
        `MarkdownView.as_view(file_name=...)`.
    :return: An absolute, normalized filesystem path, or `None` if it
        cannot be resolved (e.g. no matching file exists).
    """
    try:
        template = _get_engine().get_template(file_name)
    except Exception:
        return None
    return os.path.normpath(template.origin.name)


def _iter_markdown_view_routes(resolver, namespace_parts=()):
    """
    Recursively walk a URLResolver's patterns, yielding
    `(file_name, full_reverse_name)` for every leaf pattern whose view is a
    `MarkdownView` (or subclass) constructed with a `file_name` kwarg.

    :param resolver: A `django.urls.URLResolver` (typically the project's
        root resolver, from `django.urls.get_resolver()`).
    :param namespace_parts: Namespace segments accumulated from ancestor
        `include()` calls, used to build the fully-qualified reverse name.
    """
    # Local import to avoid a hard import-time dependency between this
    # module and `views.py` (which doesn't need to import this module at
    # module load time).
    from markdown_view.views import MarkdownView

    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            child_namespace = namespace_parts
            if pattern.namespace:
                child_namespace = namespace_parts + (pattern.namespace,)
            yield from _iter_markdown_view_routes(pattern, child_namespace)
            continue

        callback = getattr(pattern, "callback", None)
        view_class = getattr(callback, "view_class", None)
        if not (isinstance(view_class, type) and issubclass(view_class, MarkdownView)):
            continue

        file_name = getattr(callback, "view_initkwargs", {}).get("file_name")
        if not file_name or not pattern.name:
            # No `file_name`, or an unnamed route we can't `reverse()`.
            continue

        full_name = ":".join((*namespace_parts, pattern.name))
        yield file_name, full_name


def build_markdown_view_url_registry(resolver=None):
    """
    Build a `{absolute source file path: URL}` mapping for every registered
    `MarkdownView` (or subclass) route in the project, by walking the
    resolved root URLconf.

    :param resolver: A `django.urls.URLResolver` to walk. Defaults to
        `django.urls.get_resolver()` (the project's root resolver).
    :return: dict mapping each route's absolute source file path to the
        URL that serves it.
    """
    if resolver is None:
        resolver = get_resolver()

    registry = {}
    for file_name, full_name in _iter_markdown_view_routes(resolver):
        source_path = resolve_markdown_source_path(file_name)
        if source_path is None:
            logger.debug(
                "markdown_view: route %r references file_name %r, which "
                "could not be resolved to a source file; skipping.",
                full_name, file_name,
            )
            continue
        try:
            url = reverse(full_name)
        except NoReverseMatch:
            logger.debug(
                "markdown_view: could not reverse %r for file_name %r; "
                "skipping (likely behind a required URL argument).",
                full_name, file_name,
            )
            continue
        registry[source_path] = url
    return registry


def get_markdown_view_url_registry(force_refresh=False):
    """
    Return the (cached) `{absolute source file path: URL}` registry for the
    currently active URLconf, building it on first access.

    :param force_refresh: Rebuild the registry even if a cached copy exists.
    :return: dict mapping each route's absolute source file path to the URL
        that serves it.
    """
    resolver = get_resolver()
    cache_key = id(resolver)
    if force_refresh or cache_key not in _registry_cache:
        _registry_cache[cache_key] = build_markdown_view_url_registry(resolver)
    return _registry_cache[cache_key]


def clear_markdown_view_url_registry_cache():
    """Clear all cached URL registries. Primarily useful in tests."""
    _registry_cache.clear()


_HREF_RE = re.compile(r'(<a\b[^>]*\bhref=")([^"]*)(")', re.IGNORECASE)


def rewrite_markdown_links(html, source_path, registry=None):
    """
    Rewrite `<a href="...">` targets in rendered markdown HTML that point
    at other markdown source files -- via a plain, filesystem-relative
    link resolved relative to `source_path`'s directory -- to the actual
    routed URL of the `MarkdownView` serving that file, if one is
    registered.

    Links that are absolute (have a scheme, start with `/`, or are
    fragment-only/`mailto:`) or don't target a `.md` file are left
    untouched, as are relative `.md` links with no matching registered
    route (they render exactly as markdown would otherwise produce).

    :param html: Rendered HTML markup, already converted from Markdown.
    :param source_path: Absolute filesystem path of the `.md` file `html`
        was rendered from; used to resolve relative link targets.
    :param registry: An optional pre-built `{absolute path: URL}` registry.
        Built via `get_markdown_view_url_registry()` if not provided.
    :return: The HTML with resolvable internal links rewritten.
    """
    if registry is None:
        registry = get_markdown_view_url_registry()
    source_dir = os.path.dirname(source_path)

    def _replace(match):
        prefix, href, suffix = match.groups()
        target, _, fragment = href.partition("#")
        if not target or "://" in target or target.startswith(("/", "mailto:")):
            return match.group(0)
        if not target.lower().endswith(".md"):
            return match.group(0)

        resolved_path = os.path.normpath(os.path.join(source_dir, target))
        url = registry.get(resolved_path)
        if url is None:
            logger.debug(
                "markdown_view: no registered route for linked file %r "
                "(resolved from %r while rendering %r).",
                resolved_path, href, source_path,
            )
            return match.group(0)

        new_href = f"{url}#{fragment}" if fragment else url
        return f"{prefix}{new_href}{suffix}"

    return _HREF_RE.sub(_replace, html)
