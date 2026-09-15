"""URL configuration used only by markdown_view's own test suite.

Registers a variety of ``MarkdownView`` (and subclass) routes, plus a few
routes intentionally shaped to exercise ``registry.py``'s edge cases (no
``name=``, a required URL argument, namespacing, a non-``MarkdownView``
callback, and two differently-named routes serving the same source file).
"""
from django.urls import include, path
from django.views.generic import TemplateView

from markdown_view.views import (
    LoggedInMarkdownView,
    MarkdownView,
    StaffMarkdownView,
)

# Two levels of `include()` nesting, to exercise `registry.py`'s namespace
# accumulation walk.
level2_patterns = (
    [
        path(
            "readme/",
            MarkdownView.as_view(file_name="testapp/NESTED.md"),
            name="nested_readme",
        ),
    ],
    "level2",
)

level1_patterns = (
    [
        path("level2/", include(level2_patterns, namespace="level2")),
    ],
    "level1",
)

urlpatterns = [
    path(
        "readme/",
        MarkdownView.as_view(file_name="testapp/README.md"),
        name="readme",
    ),
    path(
        "other/",
        MarkdownView.as_view(file_name="testapp/docs/OTHER.md"),
        name="other",
    ),
    path(
        "logged-in/",
        LoggedInMarkdownView.as_view(file_name="testapp/LOGGED_IN.md"),
        name="logged_in",
    ),
    path(
        "staff/",
        StaffMarkdownView.as_view(file_name="testapp/STAFF.md"),
        name="staff",
    ),
    # No `name=`: `registry.py` must skip this route since it can't be
    # `reverse()`d.
    path("noname/", MarkdownView.as_view(file_name="testapp/README.md")),
    # Not a `MarkdownView` (sub)class: `registry.py` must skip this route.
    path(
        "plain/",
        TemplateView.as_view(template_name="markdown_view/markdown.html"),
        name="plain",
    ),
    # Required URL argument, and never linked from any fixture `.md` file:
    # `registry.py` must skip it (can't `reverse()` without an argument).
    path(
        "<int:pk>/context/",
        MarkdownView.as_view(file_name="testapp/CONTEXT_TEST.md"),
        name="context_test",
    ),
    # Backed by a file_name with no matching source file on disk:
    # `registry.py` must resolve to None and skip it.
    path(
        "missing/",
        MarkdownView.as_view(file_name="testapp/DOES_NOT_EXIST.md"),
        name="missing_source",
    ),
    # Two differently-named routes serving the *same* source file:
    # `registry.py` must keep the first (`readme`) and skip this alias.
    path(
        "readme-alias/",
        MarkdownView.as_view(file_name="testapp/README.md"),
        name="readme_alias",
    ),
    path("level1/", include(level1_patterns, namespace="level1")),
    # Always serves `file_name="readme.md"`, resolved relative to whatever
    # `MARKDOWN_VIEW_LOADERS` is active (rather than the fixed `testapp/`
    # app). Used by
    # `test_registry.GetMarkdownViewUrlRegistryLoaderInvalidationTests` to
    # prove the registry cache invalidates when `MARKDOWN_VIEW_LOADERS`
    # changes even though this URLconf/resolver doesn't.
    path(
        "loader-readme/",
        MarkdownView.as_view(file_name="readme.md"),
        name="loader_test_readme",
    ),
]
