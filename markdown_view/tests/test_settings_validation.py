"""
Covers `markdown_view.checks.SETTINGS_TYPES` validation, wired up as a
Django system check (`markdown_view_check`, registered against
`Tags.security` in `apps.py`) rather than validated at import time -- this
makes it directly testable with `override_settings`.
"""
from django.test import SimpleTestCase, override_settings

from markdown_view.checks import SETTINGS_TYPES, markdown_view_check


class SettingsTypeValidationTests(SimpleTestCase):
    def test_valid_settings_produce_no_errors(self):
        with override_settings(
            MARKDOWN_VIEW_LOADERS=["markdown_view.loaders.MarkdownLoader"],
            MARKDOWN_VIEW_LOADER_TEMPLATES_DIR="",
            MARKDOWN_VIEW_EXTENSIONS=["tables"],
            MARKDOWN_VIEW_BASE_DIR="/tmp",
            MARKDOWN_VIEW_TEMPLATE="markdown_view/markdown.html",
            MARKDOWN_VIEW_TEMPLATE_USE_TOC=True,
            MARKDOWN_VIEW_TEMPLATE_USE_HIGHLIGHT_JS=True,
            MARKDOWN_VIEW_USE_REQUEST_CONTEXT=False,
            MARKDOWN_VIEW_EXTRA_CONTEXT={},
            MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS=True,
            MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT="https://example.com/blob/main/",
        ):
            self.assertEqual(markdown_view_check(app_configs=[]), [])

    def test_valid_settings_produce_no_errors_with_unresolved_link_root_none(self):
        # `None` is the documented "disabled" value for this setting, and
        # is explicitly valid, unlike every other setting in SETTINGS_TYPES.
        with override_settings(MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT=None):
            self.assertEqual(markdown_view_check(app_configs=[]), [])

    def test_wrong_type_produces_an_error_for_every_setting(self):
        # `None` isn't a valid value for any of these settings, except
        # `MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT`, which explicitly treats
        # `None` as "no fallback root configured" -- so this drives one
        # `checks.Error` per declared setting other than that one.
        none_tolerant_settings = {"MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT"}
        overrides = {name: None for name in SETTINGS_TYPES}
        with override_settings(**overrides):
            errors = markdown_view_check(app_configs=[])
        self.assertEqual(
            len(errors), len(SETTINGS_TYPES) - len(none_tolerant_settings)
        )
        for error in errors:
            self.assertEqual(error.id, "markdown_view.E001")
        self.assertNotIn(
            "MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT",
            " ".join(error.msg for error in errors),
        )

    def test_unresolved_link_root_wrong_type(self):
        with override_settings(MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT=123):
            errors = markdown_view_check(app_configs=[])
        self.assertEqual(len(errors), 1)
        self.assertIn("MARKDOWN_VIEW_UNRESOLVED_LINK_ROOT", errors[0].msg)

    def test_bool_setting_wrong_type(self):
        with override_settings(MARKDOWN_VIEW_TEMPLATE_USE_TOC="not-a-bool"):
            errors = markdown_view_check(app_configs=[])
        self.assertEqual(len(errors), 1)
        self.assertIn(
            "MARKDOWN_VIEW_TEMPLATE_USE_TOC", errors[0].msg
        )

    def test_dict_setting_wrong_type(self):
        with override_settings(MARKDOWN_VIEW_EXTRA_CONTEXT=["not", "a", "dict"]):
            errors = markdown_view_check(app_configs=[])
        self.assertEqual(len(errors), 1)
        self.assertIn("MARKDOWN_VIEW_EXTRA_CONTEXT", errors[0].msg)

    def test_setting_not_defined_is_not_an_error(self):
        # Optional settings that simply aren't set shouldn't be flagged.
        self.assertEqual(markdown_view_check(app_configs=[]), [])
