import os

from django.template import Engine, TemplateDoesNotExist
from django.test import SimpleTestCase

from markdown_view.loading import load_markdown_source

TESTAPP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testapp")


def _get_engine():
    return Engine(loaders=["markdown_view.loaders.MarkdownLoader"])


class LoadMarkdownSourceTests(SimpleTestCase):
    def test_returns_raw_source_and_path_for_valid_file(self):
        source_text, source_path = load_markdown_source(
            "testapp/README.md", _get_engine()
        )
        self.assertIn("# Test App README", source_text)
        self.assertEqual(source_path, os.path.join(TESTAPP_DIR, "README.md"))

    def test_raises_template_does_not_exist_for_missing_file(self):
        with self.assertRaises(TemplateDoesNotExist):
            load_markdown_source("testapp/DOES_NOT_EXIST.md", _get_engine())

    def test_does_not_compile_raw_source_as_a_template(self):
        # Regression test: `engine.get_template(...)` would eagerly compile
        # a file's raw, pre-Markdown-conversion contents as a Django
        # template and raise `TemplateSyntaxError` here, since
        # ESCAPING_TEST.md's raw source contains literal `{% include ... %}`
        # text. `load_markdown_source()` must read the same file without
        # triggering that compilation.
        source_text, _ = load_markdown_source(
            "testapp/ESCAPING_TEST.md", _get_engine()
        )
        self.assertIn("{% include 'whatever.html' %}", source_text)
