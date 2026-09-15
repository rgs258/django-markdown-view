import os

from django.template import Engine
from django.test import SimpleTestCase, override_settings

from markdown_view.loaders import MarkdownLoader

TESTAPP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testapp")


def _get_loader():
    engine = Engine(loaders=["markdown_view.loaders.MarkdownLoader"])
    return engine.template_loaders[0]


class MarkdownLoaderGetDirsTests(SimpleTestCase):
    def test_includes_app_template_dirs(self):
        loader = _get_loader()
        dirs = [str(d) for d in loader.get_dirs()]
        self.assertIn(TESTAPP_DIR, dirs)

    @override_settings(MARKDOWN_VIEW_BASE_DIR="/tmp/some-markdown-base-dir")
    def test_includes_markdown_view_base_dir_when_set(self):
        loader = _get_loader()
        dirs = [str(d) for d in loader.get_dirs()]
        self.assertIn("/tmp/some-markdown-base-dir", dirs)

    def test_includes_base_dir_when_markdown_view_base_dir_not_set(self):
        # markdown_view/tests/settings.py sets BASE_DIR but not
        # MARKDOWN_VIEW_BASE_DIR, so BASE_DIR should be used as a fallback.
        from django.conf import settings

        loader = _get_loader()
        dirs = [str(d) for d in loader.get_dirs()]
        self.assertIn(settings.BASE_DIR, dirs)


class MarkdownLoaderGetTemplateSourcesTests(SimpleTestCase):
    def test_yields_one_origin_for_valid_name(self):
        loader = _get_loader()
        origins = list(loader.get_template_sources("testapp/README.md"))
        self.assertEqual(len(origins), 1)
        self.assertEqual(
            os.path.normpath(origins[0].name),
            os.path.join(TESTAPP_DIR, "README.md"),
        )

    def test_yields_one_origin_for_nested_valid_name(self):
        loader = _get_loader()
        origins = list(loader.get_template_sources("testapp/docs/OTHER.md"))
        self.assertEqual(len(origins), 1)
        self.assertEqual(
            os.path.normpath(origins[0].name),
            os.path.join(TESTAPP_DIR, "docs", "OTHER.md"),
        )

    def test_yields_nothing_for_non_md_name(self):
        loader = _get_loader()
        origins = list(loader.get_template_sources("testapp/notes.txt"))
        self.assertEqual(origins, [])

    def test_does_not_raise_for_path_escaping_template_dir(self):
        loader = _get_loader()
        # Attempts to escape testapp/'s directory via `..`; the
        # SuspiciousFileOperation guard should be swallowed, yielding
        # nothing rather than raising.
        origins = list(loader.get_template_sources("testapp/../secret.md"))
        self.assertEqual(origins, [])
