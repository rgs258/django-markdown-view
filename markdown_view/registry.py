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
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.template import Engine, TemplateDoesNotExist
from django.urls import NoReverseMatch, URLResolver, get_resolver, reverse

from markdown_view.constants import DEFAULT_MARKDOWN_VIEW_LOADERS

logger = logging.getLogger(__name__)

# Cached {id(resolver): {absolute file path: full reverse name}} registries.
# Keyed by the resolver's identity (Django itself caches `get_resolver()` per
# urlconf, so this naturally rebuilds if `ROOT_URLCONF`/the active urlconf
# ever changes, e.g. under `override_settings` in tests). Note that the
# *reverse name* is cached here, not the result of calling `reverse()` on
# it -- `reverse()` can depend on request/runtime context (e.g. the active
# language under `i18n_patterns()`, or the active script prefix), so it must
# be called fresh every time a link is actually rewritten.
_registry_cache = {}


def _build_engine():
    """
    Return a new `Engine` configured with the same template loaders
    `MarkdownView` itself uses, so relative `file_name` values resolve
    identically here and at render time. Built fresh (not cached at module
    scope) so it always reflects the current `MARKDOWN_VIEW_LOADERS` setting,
    e.g. under `override_settings` in tests.
    """
    return Engine(
        loaders=getattr(
            settings, "MARKDOWN_VIEW_LOADERS", DEFAULT_MARKDOWN_VIEW_LOADERS
        )
    )


def resolve_markdown_source_path(file_name, engine=None):
    """
    Resolve a markdown_view `file_name` to the absolute filesystem path of
    its underlying source file, using the same template-loader resolution
    `MarkdownView` uses to actually load and render it.

    :param file_name: A `file_name` value, as passed to
        `MarkdownView.as_view(file_name=...)`.
    :param engine: An optional `django.template.Engine` to resolve
        `file_name` with. Built via `_build_engine()` if not provided.
    :return: An absolute, normalized filesystem path, or `None` if it
        cannot be resolved (e.g. no matching file exists).
    """
    if engine is None:
        engine = _build_engine()
    try:
        template = engine.get_template(file_name)
    except TemplateDoesNotExist:
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
            # A nested `include()` -- recurse into it, extending the
            # namespace path if this include() was itself namespaced.
            child_namespace = namespace_parts
            if pattern.namespace:
                child_namespace = namespace_parts + (pattern.namespace,)
            yield from _iter_markdown_view_routes(pattern, child_namespace)
            continue

        # Leaf pattern (an actual URL, not a nested urlconf). Only
        # `as_view()`-based class-based views expose `view_class`/
        # `view_initkwargs` on their callback -- function views and
        # views wrapped by decorators that don't forward these
        # attributes will simply have `view_class=None` and get skipped
        # below.
        callback = getattr(pattern, "callback", None)
        view_class = getattr(callback, "view_class", None)
        if not (isinstance(view_class, type) and issubclass(view_class, MarkdownView)):
            continue

        file_name = getattr(callback, "view_initkwargs", {}).get("file_name")
        if not file_name or not pattern.name:
            # No `file_name`, or an unnamed route we can't `reverse()`.
            continue

        # Build the fully-qualified name (e.g. "users:support:readme")
        # needed to `reverse()` this route later, since `pattern.name`
        # alone is only unique within its own urlconf.
        full_name = ":".join((*namespace_parts, pattern.name))
        yield file_name, full_name


def build_markdown_view_url_registry(resolver=None):
    """
    Build a `{absolute source file path: full reverse name}` mapping for
    every registered `MarkdownView` (or subclass) route in the project, by
    walking the resolved root URLconf.

    Note that this stores the *reverse name* for each route, not the result
    of calling `reverse()` on it -- `reverse()`'s result can depend on
    request/runtime context (e.g. the active language under
    `i18n_patterns()`, or the active script prefix), so it must be called
    fresh at the point a link is actually rewritten, not cached here.

    :param resolver: A `django.urls.URLResolver` to walk. Defaults to
        `django.urls.get_resolver()` (the project's root resolver).
    :return: dict mapping each route's absolute source file path to the
        full reverse name (e.g. `"users:support:readme"`) that serves it.
    """
    if resolver is None:
        resolver = get_resolver()

    engine = _build_engine()
    registry = {}
    for file_name, full_name in _iter_markdown_view_routes(resolver):
        # Map the route to the file it serves by resolving `file_name`
        # (e.g. "users/README.md") through the same loader MarkdownView
        # itself uses, so the key here matches the `source_path` that
        # `rewrite_markdown_links()` will later look up against it.
        source_path = resolve_markdown_source_path(file_name, engine=engine)
        if source_path is None:
            logger.debug(
                "markdown_view: route %r references file_name %r, which "
                "could not be resolved to a source file; skipping.",
                full_name, file_name,
            )
            continue
        try:
            # Routes behind a required URL argument (e.g.
            # "<int:pk>/readme/") can't be reversed without knowing that
            # argument's value, so they're simply not linkable targets.
            # The result is only used here to confirm reversibility --
            # it's discarded rather than cached, since `reverse()` must be
            # called fresh (with the active request's language/script
            # prefix, etc.) whenever a link is actually rewritten.
            reverse(full_name)
        except NoReverseMatch:
            logger.debug(
                "markdown_view: could not reverse %r for file_name %r; "
                "skipping (likely behind a required URL argument).",
                full_name, file_name,
            )
            continue
        if source_path in registry:
            # The same source file is served by more than one route. There's
            # no inherently correct answer here, so we make the choice
            # explicit: the first route encountered wins, and later aliases
            # are logged rather than silently overriding it -- adding a
            # later alias shouldn't unexpectedly change all of a file's
            # internal links to the new alias.
            logger.debug(
                "markdown_view: file_name %r is already routed to %r; "
                "ignoring additional route %r for the same file.",
                file_name, registry[source_path], full_name,
            )
            continue
        registry[source_path] = full_name
    return registry


def get_markdown_view_url_registry(force_refresh=False):
    """
    Return the (cached) `{absolute source file path: full reverse name}`
    registry for the currently active URLconf, building it on first access.

    :param force_refresh: Rebuild the registry even if a cached copy exists.
    :return: dict mapping each route's absolute source file path to the
        full reverse name that serves it.
    """
    resolver = get_resolver()
    # `get_resolver()` is itself cached per-urlconf by Django, so keying
    # on its identity means this registry naturally rebuilds if the
    # active urlconf ever changes (e.g. `ROOT_URLCONF` swapped via
    # `override_settings` in tests) without needing to track that
    # explicitly.
    cache_key = id(resolver)
    if force_refresh or cache_key not in _registry_cache:
        _registry_cache[cache_key] = build_markdown_view_url_registry(resolver)
    return _registry_cache[cache_key]


def clear_markdown_view_url_registry_cache():
    """Clear all cached URL registries. Primarily useful in tests."""
    _registry_cache.clear()


# Matches an `<a href="...">` opening tag, capturing the text before the
# href value (group 1), the href value itself (group 2), and the closing
# quote (group 3), so `_replace()` below can substitute just the middle
# group back into the original tag without disturbing anything else on
# the `<a>` tag (other attributes, casing, etc.).
_HREF_RE = re.compile(r'(<a\b[^>]*\bhref=")([^"]*)(")', re.IGNORECASE)


def rewrite_markdown_links(html, source_path, registry=None):
    """
    Rewrite `<a href="...">` targets in rendered markdown HTML that point
    at other markdown source files -- via a plain, filesystem-relative
    link resolved relative to `source_path`'s directory -- to the actual
    routed URL of the `MarkdownView` serving that file, if one is
    registered.

    Links that are absolute (have a scheme or network location, or start
    with `/`) or don't target a `.md` file are left untouched, as are
    relative `.md` links with no matching registered route (they render
    exactly as markdown would otherwise produce). Any query string or
    `#fragment` on the original link is preserved on the rewritten URL.

    :param html: Rendered HTML markup, already converted from Markdown.
    :param source_path: Absolute filesystem path of the `.md` file `html`
        was rendered from; used to resolve relative link targets.
    :param registry: An optional pre-built `{absolute path: full reverse
        name}` registry. Built via `get_markdown_view_url_registry()` if
        not provided.
    :return: The HTML with resolvable internal links rewritten.
    """
    if registry is None:
        registry = get_markdown_view_url_registry()
    # Relative links in the source `.md` file are resolved the same way a
    # browser or file manager would: relative to the directory the *source
    # file* lives in, not relative to the URL the rendered page happens to
    # be served at.
    source_dir = os.path.dirname(source_path)

    def _replace(match):
        prefix, href, suffix = match.groups()
        # Use real URL parsing rather than string tests, so query strings
        # and fragments on otherwise-relative `.md` links (e.g.
        # `guide.md?format=print#section`) are recognized and preserved,
        # while links with a scheme (`mailto:`, `tel:`, `custom-scheme:`,
        # `https://...`) or netloc, or that are site-root-relative, are
        # correctly left alone.
        parts = urlsplit(href)
        if parts.scheme or parts.netloc or parts.path.startswith("/"):
            # Already absolute -- nothing for us to resolve, leave as-is.
            return match.group(0)
        if not parts.path.lower().endswith(".md"):
            # Not a link to another markdown source file (e.g. an image,
            # a `.txt` file, an in-page anchor) -- leave as-is.
            return match.group(0)

        # Resolve the relative path exactly as the browser would if this
        # were a raw file link, then see if some route serves that exact
        # file.
        resolved_path = os.path.normpath(os.path.join(source_dir, parts.path))
        full_name = registry.get(resolved_path)
        if full_name is None:
            # Points at a real .md file, but nothing routes it -- leave
            # the link exactly as Markdown would otherwise have rendered
            # it, rather than producing a broken URL of our own.
            logger.debug(
                "markdown_view: no registered route for linked file %r "
                "(resolved from %r while rendering %r).",
                resolved_path, href, source_path,
            )
            return match.group(0)

        try:
            # Resolved fresh on every call (rather than cached), since
            # `reverse()`'s result can depend on request/runtime context --
            # e.g. the currently active language under `i18n_patterns()`,
            # or the active script prefix -- not just the URLconf.
            url = reverse(full_name)
        except NoReverseMatch:
            # The registry is stale relative to the active URLconf (e.g. it
            # changed since the registry was built) -- leave as-is rather
            # than producing a broken link.
            logger.debug(
                "markdown_view: could not reverse %r for linked file %r "
                "while rendering %r; leaving link unrewritten.",
                full_name, resolved_path, source_path,
            )
            return match.group(0)

        new_href = urlunsplit(("", "", url, parts.query, parts.fragment))
        return f"{prefix}{new_href}{suffix}"

    return _HREF_RE.sub(_replace, html)
