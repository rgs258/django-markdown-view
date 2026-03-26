from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import RequestFactory, SimpleTestCase, override_settings

from markdown_view.views import MarkdownView


class MarkdownViewTOCTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/docs/")

    def test_toc_without_headers_does_not_error(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_name = "docs/README.md"
            (temp_path / "README.md").write_text("plain content without headers", encoding="utf-8")

            view = MarkdownView.as_view(file_name=file_name)
            with override_settings(MARKDOWN_VIEW_BASE_DIR=temp_path):
                response = view(self.request)
                response.render()

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context_data["use_toc"])
            self.assertIn("markdown_toc", response.context_data)
            self.assertNotIn("page_title", response.context_data)
