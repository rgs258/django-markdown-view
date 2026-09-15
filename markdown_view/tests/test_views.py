"""
Regression tests for `MarkdownView`'s TOC/`page_title` handling, in
particular that rendering a markdown file with no headers doesn't raise an
`IndexError` when `MARKDOWN_VIEW_TEMPLATE_USE_TOC` is enabled (the default).
"""
import os

from django.test import RequestFactory, SimpleTestCase, override_settings

from markdown_view.views import MarkdownView

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "toc")

LOADERS = [
    (
        "django.template.loaders.filesystem.Loader",
        [FIXTURES_DIR],
    ),
]


@override_settings(MARKDOWN_VIEW_LOADERS=LOADERS)
class MarkdownViewTOCTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")

    def test_toc_without_headers_does_not_error(self):
        view = MarkdownView.as_view(file_name="without_headers.md")
        response = view(self.request)
        response.render()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context_data["use_toc"])
        self.assertIn("markdown_toc", response.context_data)
        self.assertNotIn("page_title", response.context_data)

    def test_toc_with_headers_still_sets_page_title(self):
        view = MarkdownView.as_view(file_name="with_headers.md")
        response = view(self.request)
        response.render()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context_data["use_toc"])
        self.assertIn("markdown_toc", response.context_data)
        self.assertEqual(response.context_data["page_title"], "A Heading")

    def test_toc_without_headers_and_disabled_use_toc_omits_toc_context(self):
        with override_settings(MARKDOWN_VIEW_TEMPLATE_USE_TOC=False):
            view = MarkdownView.as_view(file_name="without_headers.md")
            response = view(self.request)
            response.render()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context_data["use_toc"])
        self.assertNotIn("markdown_toc", response.context_data)
        self.assertNotIn("page_title", response.context_data)
