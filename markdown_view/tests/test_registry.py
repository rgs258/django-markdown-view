"""
Regression tests for `markdown_view.registry`'s URL registry cache, in
particular that it correctly invalidates when `MARKDOWN_VIEW_LOADERS`
changes (e.g. via `override_settings` in tests), even though the active
URLconf/resolver hasn't itself changed.
"""
import os

from django.test import SimpleTestCase, override_settings

from markdown_view.registry import (
    clear_markdown_view_url_registry_cache,
    get_markdown_view_url_registry,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

LOADERS_A = [
    (
        "django.template.loaders.filesystem.Loader",
        [os.path.join(FIXTURES_DIR, "loaders_a")],
    ),
]
LOADERS_B = [
    (
        "django.template.loaders.filesystem.Loader",
        [os.path.join(FIXTURES_DIR, "loaders_b")],
    ),
]

README_A = os.path.normpath(
    os.path.join(FIXTURES_DIR, "loaders_a", "readme.md")
)
README_B = os.path.normpath(
    os.path.join(FIXTURES_DIR, "loaders_b", "readme.md")
)


class GetMarkdownViewUrlRegistryLoaderInvalidationTests(SimpleTestCase):
    """
    `readme/` (see `markdown_view/tests/urls.py`) always serves
    `file_name="readme.md"`, so which absolute file it resolves to --
    and therefore which `source_path` key the registry files it under --
    depends entirely on the active `MARKDOWN_VIEW_LOADERS`, not on
    `ROOT_URLCONF`. That makes it a minimal repro for the stale-registry
    bug: the resolver's identity never changes across these calls, so
    without explicit invalidation on `MARKDOWN_VIEW_LOADERS` changes, the
    id(resolver)-keyed cache would keep serving the registry built under
    whichever loaders were active on the *first* call.
    """

    def setUp(self):
        # The registry cache is a module-level global; make sure tests
        # don't leak into each other or into other test modules.
        clear_markdown_view_url_registry_cache()
        self.addCleanup(clear_markdown_view_url_registry_cache)

    @override_settings(MARKDOWN_VIEW_LOADERS=LOADERS_A)
    def test_registry_rebuilds_when_loaders_setting_changes(self):
        registry = get_markdown_view_url_registry()
        self.assertIn(README_A, registry)
        self.assertNotIn(README_B, registry)

        # Switch loaders without touching ROOT_URLCONF/the resolver, and
        # call get_markdown_view_url_registry() the normal way -- i.e.
        # *without* force_refresh=True. If the cache were still keyed
        # solely on resolver identity, this would return the stale
        # registry built above under LOADERS_A.
        with self.settings(MARKDOWN_VIEW_LOADERS=LOADERS_B):
            registry = get_markdown_view_url_registry()

        self.assertIn(README_B, registry)
        self.assertNotIn(README_A, registry)

    @override_settings(MARKDOWN_VIEW_LOADERS=LOADERS_A)
    def test_registry_stays_cached_when_unrelated_setting_changes(self):
        registry = get_markdown_view_url_registry()
        self.assertIn(README_A, registry)

        # An unrelated setting changing shouldn't force a rebuild -- the
        # cached registry object should be reused as-is.
        with self.settings(MARKDOWN_VIEW_TEMPLATE="some/other/template.html"):
            self.assertIs(get_markdown_view_url_registry(), registry)
