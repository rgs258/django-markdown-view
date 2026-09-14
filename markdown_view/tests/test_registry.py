"""
Focused, granular tests for `markdown_view/registry.py`, exercised directly
rather than only through a rendered view.
"""
import os

from django.test import SimpleTestCase, override_settings
from django.urls import NoReverseMatch, get_resolver

from markdown_view import registry

TESTAPP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testapp")


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
        built = registry.build_markdown_view_url_registry()
        self.assertEqual(built[_testapp_path("README.md")], "/readme/")
        self.assertEqual(built[_testapp_path("docs", "OTHER.md")], "/other/")
        self.assertEqual(built[_testapp_path("LOGGED_IN.md")], "/logged-in/")
        self.assertEqual(built[_testapp_path("STAFF.md")], "/staff/")

    def test_resolves_through_two_levels_of_namespaced_include(self):
        built = registry.build_markdown_view_url_registry()
        self.assertEqual(
            built[_testapp_path("NESTED.md")], "/level1/level2/readme/"
        )

    def test_skips_route_with_no_name(self):
        built = registry.build_markdown_view_url_registry()
        # "testapp/README.md" is also served (with a name) at "/readme/";
        # the unnamed route pointing at the same file must not overwrite or
        # duplicate that mapping with anything unreversable.
        self.assertEqual(built[_testapp_path("README.md")], "/readme/")

    def test_skips_route_requiring_url_argument(self):
        built = registry.build_markdown_view_url_registry()
        self.assertNotIn(_testapp_path("CONTEXT_TEST.md"), built)

    def test_skips_non_markdown_view_callback(self):
        # The "plain" route uses a plain TemplateView, not a MarkdownView,
        # and isn't backed by any of our fixture files, so nothing in the
        # registry should ever point at "/plain/".
        built = registry.build_markdown_view_url_registry()
        self.assertNotIn("/plain/", built.values())

    def test_skips_route_with_unresolvable_source_file(self):
        built = registry.build_markdown_view_url_registry()
        self.assertNotIn("/missing/", built.values())

    def test_iter_markdown_view_routes_finds_expected_entries(self):
        resolver = get_resolver()
        found = dict(registry._iter_markdown_view_routes(resolver))
        self.assertEqual(found["testapp/README.md"], "readme")
        self.assertEqual(found["testapp/docs/OTHER.md"], "other")
        self.assertEqual(found["testapp/NESTED.md"], "level1:level2:nested_readme")


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


class RewriteMarkdownLinksTests(SimpleTestCase):
    def setUp(self):
        self.source_path = _testapp_path("README.md")
        self.test_registry = {
            _testapp_path("docs", "OTHER.md"): "/other/",
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

    def test_leaves_non_md_relative_link_unchanged(self):
        html = '<a href="notes.txt">Notes</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_leaves_fragment_only_link_unchanged(self):
        html = '<a href="#section-one">Jump</a>'
        self.assertEqual(self._rewrite(html), html)

    def test_uses_default_registry_when_not_provided(self):
        registry.clear_markdown_view_url_registry_cache()
        html = '<a href="docs/OTHER.md">See also</a>'
        result = registry.rewrite_markdown_links(html, self.source_path)
        self.assertEqual(result, '<a href="/other/">See also</a>')
