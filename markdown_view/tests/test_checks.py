from django.test import SimpleTestCase

from markdown_view.checks import markdown_view_check


class MarkdownViewCheckTests(SimpleTestCase):
    def test_returns_empty_list_for_valid_settings(self):
        # markdown_view/tests/settings.py doesn't define any of the
        # optional MARKDOWN_VIEW_* settings, so there's nothing to flag.
        self.assertEqual(markdown_view_check(app_configs=[]), [])
