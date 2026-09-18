from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from markdown_view import registry

User = get_user_model()


class MarkdownViewRenderingTests(TestCase):
    def setUp(self):
        registry.clear_markdown_view_url_registry_cache()
        self.addCleanup(registry.clear_markdown_view_url_registry_cache)

    def test_renders_200_with_converted_markdown_content(self):
        response = self.client.get(reverse("readme"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Table converted to HTML.
        self.assertIn("<table>", content)
        self.assertIn("<td>1</td>", content)
        # Fenced code block converted to HTML.
        self.assertIn('<pre><code class="language-python">', content)
        self.assertIn("def hello():", content)

    def test_none_file_name_does_not_raise_or_render_markdown(self):
        # A bare MarkdownView with no file_name falls through to base
        # TemplateView behavior.
        from django.test import RequestFactory

        from markdown_view.views import MarkdownView

        request = RequestFactory().get("/")
        view = MarkdownView()
        view.setup(request)
        context = view.get_context_data()
        self.assertNotIn("markdown_content", context)

    def test_context_data_defaults(self):
        response = self.client.get(reverse("readme"))
        context = response.context
        self.assertIn("markdown_content", context)
        self.assertEqual(context["use_highlight_js"], True)
        self.assertEqual(context["use_toc"], True)
        self.assertIn("markdown_toc", context)
        self.assertEqual(context["page_title"], "Test App README")

    @override_settings(MARKDOWN_VIEW_TEMPLATE_USE_TOC=False)
    def test_toc_context_absent_when_disabled(self):
        response = self.client.get(reverse("readme"))
        context = response.context
        self.assertEqual(context["use_toc"], False)
        self.assertNotIn("markdown_toc", context)
        self.assertNotIn("page_title", context)

    def test_headerless_document_renders_without_page_title(self):
        # Regression test: rendering Markdown with no headers used to raise
        # an `IndexError` when `MARKDOWN_VIEW_TEMPLATE_USE_TOC` is enabled
        # (the default), since `page_title` unconditionally indexed the
        # (empty) TOC tokens.
        response = self.client.get(reverse("no_headers"))
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context["use_toc"], True)
        self.assertIn("markdown_toc", context)
        self.assertNotIn("page_title", context)

    def test_image_extension_renders_resolvable_static_tag(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('src="/static/image.png"', content)
        self.assertNotIn('src=""', content)


class MarkdownViewRewriteInternalLinksTests(TestCase):
    def setUp(self):
        registry.clear_markdown_view_url_registry_cache()
        self.addCleanup(registry.clear_markdown_view_url_registry_cache)

    def test_default_rewrites_relative_link_to_routed_file(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('href="/other/"', content)

    def test_default_preserves_fragment_on_rewritten_link(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('href="/other/#section-two"', content)

    def test_unrouted_relative_link_left_unchanged(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('href="UNROUTED.md"', content)

    def test_absolute_and_external_and_mailto_links_left_unchanged(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('href="/somewhere/"', content)
        self.assertIn('href="https://example.com"', content)
        self.assertIn('href="mailto:someone@example.com"', content)

    def test_non_md_relative_link_left_unchanged(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('href="notes.txt"', content)

    @override_settings(MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS=False)
    def test_disabling_rewrite_leaves_routed_link_unchanged(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('href="docs/OTHER.md"', content)
        self.assertNotIn('href="/other/"', content)


class MarkdownViewUnresolvedLinkRootTests(TestCase):
    """
    End-to-end coverage (via a real rendered `MarkdownView`) of
    `MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT`, the optional fallback root for
    relative links that `MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS` can't
    resolve to a registered route.
    """

    FALLBACK_ROOT = "https://git.example.com/example/project/-/blob/main/"

    def setUp(self):
        registry.clear_markdown_view_url_registry_cache()
        self.addCleanup(registry.clear_markdown_view_url_registry_cache)

    def test_without_fallback_root_unrouted_and_non_md_links_are_unchanged(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('href="UNROUTED.md"', content)
        self.assertIn('href="notes.txt"', content)

    @override_settings(MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT=FALLBACK_ROOT)
    def test_unrouted_md_link_resolves_against_fallback_root(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn(
            'href="https://git.example.com/example/project/-/blob/main/'
            'UNROUTED.md"',
            content,
        )

    @override_settings(MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT=FALLBACK_ROOT)
    def test_non_md_link_resolves_against_fallback_root(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn(
            'href="https://git.example.com/example/project/-/blob/main/'
            'notes.txt"',
            content,
        )

    @override_settings(MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT=FALLBACK_ROOT)
    def test_registered_route_still_takes_precedence(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('href="/other/"', content)

    @override_settings(
        MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS=False,
        MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT=FALLBACK_ROOT,
    )
    def test_disabling_rewrite_also_disables_fallback(self):
        response = self.client.get(reverse("readme"))
        content = response.content.decode()
        self.assertIn('href="UNROUTED.md"', content)
        self.assertIn('href="notes.txt"', content)
        self.assertIn('href="docs/OTHER.md"', content)


class LoggedInMarkdownViewTests(TestCase):
    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("logged_in"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("logged_in"), response.url)

    def test_authenticated_user_succeeds(self):
        user = User.objects.create_user(username="alice")
        self.client.force_login(user)
        response = self.client.get(reverse("logged_in"))
        self.assertEqual(response.status_code, 200)


class StaffMarkdownViewTests(TestCase):
    def test_anonymous_is_rejected(self):
        response = self.client.get(reverse("staff"))
        # AccessMixin redirects anonymous users to login.
        self.assertEqual(response.status_code, 302)

    def test_authenticated_non_staff_is_rejected(self):
        user = User.objects.create_user(username="bob")
        self.client.force_login(user)
        response = self.client.get(reverse("staff"))
        # AccessMixin raises PermissionDenied for authenticated users who
        # fail the test, resulting in a 403.
        self.assertEqual(response.status_code, 403)

    def test_staff_user_succeeds(self):
        user = User.objects.create_user(username="carol", is_staff=True)
        self.client.force_login(user)
        response = self.client.get(reverse("staff"))
        self.assertEqual(response.status_code, 200)


class MarkdownViewRequestContextTests(TestCase):
    @override_settings(MARKDOWN_VIEW_USE_REQUEST_CONTEXT=True)
    def test_use_request_context_true_exposes_view_context(self):
        response = self.client.get(reverse("context_test", args=[42]))
        content = response.content.decode()
        self.assertIn('pk is "42"', content)

    def test_use_request_context_default_does_not_leak(self):
        response = self.client.get(reverse("context_test", args=[42]))
        content = response.content.decode()
        self.assertIn('pk is ""', content)


class MarkdownViewExtraContextTests(TestCase):
    @override_settings(
        MARKDOWN_VIEW_EXTRA_CONTEXT={"extra_context_value": "injected-value"}
    )
    def test_extra_context_available_to_template_tags(self):
        response = self.client.get(reverse("context_test", args=[42]))
        content = response.content.decode()
        self.assertIn('extra is "injected-value"', content)
