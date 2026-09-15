"""
Focused, granular tests for `markdown_view/registry.py`, exercised directly
rather than only through a rendered view.
"""
import os

from django.test import SimpleTestCase, override_settings
from django.urls import get_resolver
from django.urls.base import set_script_prefix

from markdown_view import registry

TESTAPP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testapp")
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _testapp_path(*parts):
    return os.path.normpath(os.path.join(TESTAPP_DIR, *parts))


class ResolveMarkdownSourcePathTests(SimpleTestCase):
    def test_resolves_known_file_name(self):
        self.assertEqual(
            registry.resolve_markdown_source_path("testapp/README.md"),
            _testapp_path("README.md"),
        )

    def test_resolves_nested_file_name(self):
        self.assertEqual(
            registry.resolve_markdown_source_path("testapp/docs/OTHER.md"),
            _testapp_path("docs", "OTHER.md"),
        )

    def test_returns_none_for_unknown_file_name(self):
        self.assertIsNone(
            registry.resolve_markdown_source_path("testapp/DOES_NOT_EXIST.md")
        )


class BuildMarkdownViewUrlRegistryTests(SimpleTestCase):
    def setUp(self):
        registry.clear_markdown_view_url_registry_cache()

    def test_builds_expected_mapping(self):
        # The registry maps each route's absolute source file path to its
        # *reverse name* (not an already-resolved URL) -- `reverse()` is
        # called fresh at rewrite time so it can reflect request/runtime
        # context (active script prefix, active language, etc.).
        built = registry.build_markdown_view_url_registry()
        self.assertEqual(built[_testapp_path("README.md")], "readme")
        self.assertEqual(built[_testapp_path("docs", "OTHER.md")], "other")
        self.assertEqual(built[_testapp_path("LOGGED_IN.md")], "logged_in")
        self.assertEqual(built[_testapp_path("STAFF.md")], "staff")

    def test_resolves_through_two_levels_of_namespaced_include(self):
        built = registry.build_markdown_view_url_registry()
        self.assertEqual(
            built[_testapp_path("NESTED.md")], "level1:level2:nested_readme"
        )

    def test_skips_route_with_no_name(self):
        built = registry.build_markdown_view_url_registry()
        # "testapp/README.md" is also served (with a name) at "/readme/";
        # the unnamed route pointing at the same file must not overwrite or
        # duplicate that mapping with anything unreversable.
        self.assertEqual(built[_testapp_path("README.md")], "readme")

    def test_skips_route_requiring_url_argument(self):
        built = registry.build_markdown_view_url_registry()
        self.assertNotIn(_testapp_path("CONTEXT_TEST.md"), built)

    def test_skips_non_markdown_view_callback(self):
        # The "plain" route uses a plain TemplateView, not a MarkdownView,
        # and isn't backed by any of our fixture files, so nothing in the
        # registry should ever point at "plain".
        built = registry.build_markdown_view_url_registry()
        self.assertNotIn("plain", built.values())

    def test_skips_route_with_unresolvable_source_file(self):
        built = registry.build_markdown_view_url_registry()
        self.assertNotIn("missing_source", built.values())

    def test_iter_markdown_view_routes_finds_expected_entries(self):
        # Note: `_iter_markdown_view_routes()` itself yields *every* named
        # `MarkdownView` route, including duplicates for the same source
        # file (e.g. "readme" and "readme_alias" both reference
        # "testapp/README.md") -- deduplication (first-route-wins) only
        # happens downstream, in `build_markdown_view_url_registry()`. So
        # this checks membership in the full list of pairs, rather than
        # collapsing into a dict (which would non-deterministically hide
        # duplicate entries).
        resolver = get_resolver()
        found = list(registry._iter_markdown_view_routes(resolver))
        self.assertIn(("testapp/README.md", "readme"), found)
        self.assertIn(("testapp/docs/OTHER.md", "other"), found)
        self.assertIn(
            ("testapp/NESTED.md", "level1:level2:nested_readme"), found
        )

    def test_first_route_wins_for_duplicate_source_file(self):
        # "readme" and "readme_alias" (see markdown_view/tests/urls.py) both
        # serve "testapp/README.md". The registry's documented policy is
        # explicit: the first route encountered wins, and later routes for
        # the same source file are skipped rather than silently overriding
        # it. This asserts only that externally-observable behavior, not
        # the debug logging that accompanies the skip.
        built = registry.build_markdown_view_url_registry()
        self.assertEqual(built[_testapp_path("README.md")], "readme")
        self.assertNotIn("readme_alias", built.values())


class RegistryCachingTests(SimpleTestCase):
    def setUp(self):
        registry.clear_markdown_view_url_registry_cache()
        self.addCleanup(registry.clear_markdown_view_url_registry_cache)

    def test_second_call_reuses_cache(self):
        first = registry.get_markdown_view_url_registry()
        second = registry.get_markdown_view_url_registry()
        self.assertIs(first, second)

    def test_force_refresh_rebuilds(self):
        first = registry.get_markdown_view_url_registry()
        second = registry.get_markdown_view_url_registry(force_refresh=True)
        self.assertIsNot(first, second)
        self.assertEqual(first, second)

    def test_clear_cache_forces_rebuild_on_next_call(self):
        first = registry.get_markdown_view_url_registry()
        registry.clear_markdown_view_url_registry_cache()
        second = registry.get_markdown_view_url_registry()
        self.assertIsNot(first, second)
        self.assertEqual(first, second)


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
    `loader-readme/` (see `markdown_view/tests/urls.py`) always serves
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
        registry.clear_markdown_view_url_registry_cache()
        self.addCleanup(registry.clear_markdown_view_url_registry_cache)

    @override_settings(MARKDOWN_VIEW_LOADERS=LOADERS_A)
    def test_registry_rebuilds_when_loaders_setting_changes(self):
        built = registry.get_markdown_view_url_registry()
        self.assertIn(README_A, built)
        self.assertNotIn(README_B, built)

        # Switch loaders without touching ROOT_URLCONF/the resolver, and
        # call get_markdown_view_url_registry() the normal way -- i.e.
        # *without* force_refresh=True. If the cache were still keyed
        # solely on resolver identity, this would return the stale
        # registry built above under LOADERS_A.
        with self.settings(MARKDOWN_VIEW_LOADERS=LOADERS_B):
            built = registry.get_markdown_view_url_registry()

        self.assertIn(README_B, built)
        self.assertNotIn(README_A, built)

    @override_settings(MARKDOWN_VIEW_LOADERS=LOADERS_A)
    def test_registry_stays_cached_when_unrelated_setting_changes(self):
        built = registry.get_markdown_view_url_registry()
        self.assertIn(README_A, built)

        # An unrelated setting changing shouldn't force a rebuild -- the
        # cached registry object should be reused as-is.
        with self.settings(MARKDOWN_VIEW_TEMPLATE="some/other/template.html"):
            self.assertIs(registry.get_markdown_view_url_registry(), built)


class RewriteMarkdownLinksTests(SimpleTestCase):
    def setUp(self):
        self.source_path = _testapp_path("README.md")
        self.test_registry = {
            _testapp_path("docs", "OTHER.md"): "other",
        }

    def _rewrite(self, html):
        return registry.rewrite_markdown_links(
            html, self.source_path, registry=self.test_registry
        )

    def test_rewrites_relative_link_to_routed_file(self):
        html = '<a href="docs/OTHER.md">See also</a>'
        self.assertEqual(
            self._rewrite(html), '<a href="/other/">See also</a>'
        )

    def test_preserves_fragment_on_rewritten_link(self):
        html = '<a href="docs/OTHER.md#section-two">See also</a>'
        self.assertEqual(
            self._rewrite(html), '<a href="/other/#section-two">See also</a>'
        )

    def test_preserves_query_string_on_rewritten_link(self):
        html = '<a href="docs/OTHER.md?print=1">See also</a>'
        self.assertEqual(
            self._rewrite(html), '<a href="/other/?print=1">See also</a>'
        )

    def test_preserves_query_string_and_fragment_on_rewritten_link(self):
        html = '<a href="docs/OTHER.md?print=1#section-two">See also</a>'
        self.assertEqual(
            self._rewrite(html),
            '<a href="/other/?print=1#section-two">See also</a>',
        )

    def test_leaves_unrouted_relative_md_link_unchanged(self):
        html = '<a href="UNROUTED.md">Unrouted</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_leaves_absolute_link_unchanged(self):
        html = '<a href="/somewhere/">Absolute</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_leaves_fully_qualified_url_unchanged(self):
        html = '<a href="https://example.com">External</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_leaves_mailto_link_unchanged(self):
        html = '<a href="mailto:someone@example.com">Mail</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_leaves_tel_link_unchanged(self):
        html = '<a href="tel:foo.md">Call</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_leaves_custom_scheme_link_unchanged(self):
        html = '<a href="custom-scheme:foo.md">Custom</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_leaves_non_md_relative_link_unchanged(self):
        html = '<a href="notes.txt">Notes</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_leaves_fragment_only_link_unchanged(self):
        html = '<a href="#section-one">Jump</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_leaves_link_unchanged_when_registry_entry_is_stale(self):
        # If the registry's cached reverse name no longer resolves (e.g.
        # the route was removed from the urlconf after the registry was
        # built), `reverse()` raises `NoReverseMatch` at rewrite time; the
        # link is left exactly as markdown would otherwise have rendered
        # it rather than producing a broken URL.
        stale_registry = {
            _testapp_path("docs", "OTHER.md"): "no-such-route-name",
        }
        html = '<a href="docs/OTHER.md">See also</a>'
        result = registry.rewrite_markdown_links(
            html, self.source_path, registry=stale_registry
        )
        self.assertEqual(result, html)

    def test_uses_default_registry_when_not_provided(self):
        registry.clear_markdown_view_url_registry_cache()
        html = '<a href="docs/OTHER.md">See also</a>'
        result = registry.rewrite_markdown_links(html, self.source_path)
        self.assertEqual(result, '<a href="/other/">See also</a>')


class RewriteMarkdownLinksScriptPrefixTests(SimpleTestCase):
    """
    Regression coverage for the fact that `registry.py` caches the
    *reverse name* for each route, not the result of calling `reverse()`
    on it -- `reverse()` is called fresh every time a link is actually
    rewritten, so its result can reflect request/runtime context (e.g. the
    active script prefix) that may change after the registry was
    built/cached.
    """

    def setUp(self):
        registry.clear_markdown_view_url_registry_cache()
        self.addCleanup(registry.clear_markdown_view_url_registry_cache)
        self.addCleanup(set_script_prefix, "/")

    def test_rewrite_reflects_script_prefix_active_at_rewrite_time(self):
        source_path = _testapp_path("README.md")
        html = '<a href="docs/OTHER.md">See also</a>'

        # Build/cache the registry once, under the default ("/") script
        # prefix.
        set_script_prefix("/")
        built_registry = registry.get_markdown_view_url_registry()
        first_result = registry.rewrite_markdown_links(
            html, source_path, registry=built_registry
        )
        self.assertEqual(first_result, '<a href="/other/">See also</a>')

        # Change the active script prefix -- e.g. as would happen when the
        # same project is mounted under a different path prefix -- without
        # rebuilding the registry.
        set_script_prefix("/prefix/")
        second_result = registry.rewrite_markdown_links(
            html, source_path, registry=built_registry
        )

        # The already-cached registry still stores the stable reverse
        # name ("other"), but `reverse()` is re-executed at rewrite time,
        # so the newly rewritten URL reflects the new script prefix.
        self.assertEqual(
            second_result, '<a href="/prefix/other/">See also</a>'
        )
        self.assertNotEqual(first_result, second_result)
