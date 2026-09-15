from django.core.checks import Tags, run_checks
from django.test import SimpleTestCase, override_settings

from markdown_view.checks import markdown_view_check


class MarkdownViewCheckTests(SimpleTestCase):
    def test_returns_empty_list_for_valid_settings(self):
        # markdown_view/tests/settings/coveralls_settings.py doesn't define
        # any of the optional MARKDOWN_VIEW_* settings, so there's nothing
        # to flag.
        self.assertEqual(markdown_view_check(app_configs=[]), [])


class MarkdownViewCheckRegistrationTests(SimpleTestCase):
    """
    Confirms `markdown_view_check` is actually *wired up* through Django's
    system-check framework (registered against `Tags.security` in
    `MarkdownViewConfig.ready()`, see `markdown_view/apps.py`), not just
    that the function itself behaves correctly in isolation.
    """

    def test_run_checks_surfaces_invalid_setting_via_registered_check(self):
        with override_settings(MARKDOWN_VIEW_TEMPLATE_USE_TOC="not-a-bool"):
            errors = run_checks(tags=[Tags.security])

        self.assertTrue(
            any(error.id == "markdown_view.E001" for error in errors),
            "Expected django.core.checks.run_checks() to surface "
            "markdown_view.E001 for an invalid MARKDOWN_VIEW_* setting; "
            "got: %r" % (errors,),
        )

    def test_run_checks_reports_no_markdown_view_errors_for_valid_settings(self):
        errors = run_checks(tags=[Tags.security])
        self.assertFalse(
            any(error.id == "markdown_view.E001" for error in errors)
        )
