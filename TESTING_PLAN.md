# Test Suite Implementation Plan

Tracks: [Issue #10 &mdash; "Unit Testing"](https://github.com/rgs258/django-markdown-view/issues/10)
("Write tests and set up Travis correctly")

This document is a plan, not an implementation. It is committed to the
`test-suite/issue-10-add-tests` branch (based on
`feature/rewrite-internal-markdown-links`, so tests can cover the new
`markdown_view/registry.py` link-rewriting behavior alongside everything
else) so that whoever picks up the implementation work has full context
without re-deriving it.

## Current state

- There are **zero tests** in this repository today.
- `manage.py` sets `DJANGO_SETTINGS_MODULE` to
  `markdown_view.tests.settings.coveralls_settings` &mdash; a module that
  does not exist. This was clearly the intended location for a test
  settings module and never got built out.
- `tox.ini` runs `coverage run manage.py test` across a Django/Python
  version matrix, but since there's nothing under `markdown_view/tests/`,
  this currently either fails or silently discovers zero tests.
- `.travis.yml` configures Travis CI. Travis's free tier for open source
  effectively ended some years ago; **recommend replacing Travis with
  GitHub Actions** as part of this work rather than "setting up Travis
  correctly" literally. Coveralls integration (referenced in the README
  badge) works fine from GitHub Actions too.
- `.coveragerc`'s `[run]` section has `source = markdown-view` (hyphen).
  The actual package/import name is `markdown_view` (underscore). This
  typo means coverage has likely never actually measured the package it
  claims to. Fix this alongside adding tests, or coverage numbers will be
  meaningless.
- `setup.py` declares support for `django>=2.2` and `markdown>=3.2`, with
  classifiers through Python 3.10 and "Framework :: Django :: 4". Whatever
  CI matrix is built should reflect currently-supportable combinations
  (see "Suggested CI matrix" below) rather than trying to resurrect every
  historical combination in the old `tox.ini`.

## Scaffolding needed

None of this exists yet and all of it is a prerequisite for writing actual
test cases:

1. **A minimal Django settings module for the test suite.**
   Suggest `markdown_view/tests/settings.py` (flat, not the nested
   `tests/settings/coveralls_settings.py` package `manage.py` currently
   references &mdash; simplify unless there's a reason to keep multiple
   settings variants). Needs at least:
   - `INSTALLED_APPS` including `django.contrib.auth`,
     `django.contrib.contenttypes`, `django.contrib.sessions` (for
     `LoginRequiredMixin`/`UserPassesTestMixin` login-redirect behavior),
     and `markdown_view` itself.
   - `ROOT_URLCONF` pointing at a new `markdown_view/tests/urls.py`.
   - `TEMPLATES` configuration sufficient for `MARKDOWN_VIEW_TEMPLATE`
     (`markdown_view/markdown.html`) to render, plus whatever `AUTH_*`
     settings `LoginRequiredMixin` needs (`LOGIN_URL` at minimum).
   - `MIDDLEWARE` including auth/session middleware, since the view tests
     will need an authenticated/staff request context.
   - `DATABASES` pointed at in-memory SQLite (`User`/`Session` models need
     a database even though this package's own code has none).

2. **A minimal "app under test" fixture layout.**
   The package's `MarkdownLoader` (`markdown_view/loaders.py`) locates
   `.md` files by walking `get_app_template_dirs("")` across
   `INSTALLED_APPS`, plus `BASE_DIR`/`MARKDOWN_VIEW_BASE_DIR`. To test this
   loader (and the new `registry.py`, which depends on it to resolve
   `file_name` to an absolute path) realistically, add a small fixture app,
   e.g. `markdown_view/tests/testapp/`, containing:
   - `README.md` at its root (covers the "root of an app" loader case).
   - A nested `docs/OTHER.md` (covers `MARKDOWN_VIEW_LOADER_TEMPLATES_DIR`
     and multi-segment `file_name` values like `"testapp/docs/OTHER.md"`).
   - At least one `.md` fixture containing:
     - A relative link to another fixture `.md` file that *is* routed
       (for `registry.py` positive-path coverage).
     - A relative link to a fixture `.md` file that is *not* routed at all
       (for `registry.py`'s "leave unresolvable links alone" fallback).
     - A relative link to a fixture `.md` file using a `#fragment`
       (confirms fragments are preserved through rewriting).
     - An absolute link (`/somewhere/`), a fully-qualified URL
       (`https://example.com`), and a non-`.md` relative link (e.g. an
       image or a `.txt` file), to confirm `registry.py` correctly leaves
       all of these untouched.
     - A markdown image reference, to exercise
       `markdown_extensions.ImageExtension`.
     - A fenced code block and a table, to exercise the `fenced_code` and
       `tables` extensions.
     - At least two headers, to exercise TOC generation
       (`MARKDOWN_VIEW_TEMPLATE_USE_TOC`/`page_title`).
   - `markdown_view/tests/testapp/apps.py` + `__init__.py` so it can be
     added to `INSTALLED_APPS` in the test settings module.

3. **`markdown_view/tests/urls.py`**, registering:
   - At least two `MarkdownView.as_view(file_name=...)` routes (so
     `registry.py` has more than one entry to resolve between).
   - A `LoggedInMarkdownView` route and a `StaffMarkdownView` route (to
     test the two permission mixins distinctly).
   - A `MarkdownView` route nested under a namespaced `include()`, and
     ideally one more nested two levels deep, to exercise
     `registry.py`'s namespace-accumulation walk logic
     (`_iter_markdown_view_routes`).
   - One route with a required URL argument (e.g.
     `path("<int:pk>/readme/", ...)`) whose backing view is never actually
     linked to by a fixture `.md` file, to confirt `registry.py` skips
     routes it can't `reverse()` without raising.

4. **Test settings type-validation coverage for `markdown_view/__init__.py`.**
   This module raises `ImproperlyConfigured` at *import time* based on
   `SETTINGS_TYPES`, which makes it awkward to test with the normal
   Django settings-override tools (`override_settings` doesn't re-trigger
   module-level import validation). Plan: refactor the validation into a
   function callable from a Django system check (there's already an
   underused `markdown_view/checks.py` with a stubbed no-op check) instead
   of running at import time, OR test it via a subprocess that imports the
   module fresh with bad settings and asserts the `ImproperlyConfigured`
   is raised. Flagging this as a design tension to resolve during
   implementation, not deciding it up front here.

## Test cases to write

Organize as `markdown_view/tests/test_*.py`, one file per module under
test, following the existing package layout:

### `test_views.py`

- `MarkdownView` renders 200 for a valid `file_name`, and the rendered
  HTML contains content converted from the fixture Markdown (tables,
  fenced code blocks present as expected HTML).
- `MarkdownView` with `file_name = None` doesn't attempt to load/render
  anything (falls through to base `TemplateView` behavior) and doesn't
  raise.
- `MarkdownView.get_context_data()` populates `markdown_content`,
  `use_highlight_js`, `use_toc`, `markdown_toc`, `page_title` correctly
  under default settings, and confirms `use_toc`/`markdown_toc`/
  `page_title` are absent when `MARKDOWN_VIEW_TEMPLATE_USE_TOC=False`.
- `ImageExtension` rewrites `<img src="...">` to a `{% static %}` tag that
  actually resolves when the surrounding template is rendered (i.e. no
  broken `src=""` in the final HTML).
- `LoggedInMarkdownView`: anonymous request redirects to login; any
  authenticated request succeeds (200).
- `StaffMarkdownView`: anonymous and non-staff authenticated requests are
  rejected (`UserPassesTestMixin` default behavior: redirect or 403,
  confirm which); staff request succeeds (200).
- `MARKDOWN_VIEW_USE_REQUEST_CONTEXT=True` makes request-context variables
  (e.g. a value set via a custom context processor in test settings)
  available to `{% %}` tags embedded in a fixture `.md` file; confirm the
  default (`False`) does not leak request context.
- `MARKDOWN_VIEW_EXTRA_CONTEXT` values are available for template tags
  embedded in the Markdown source.
- **New in this branch** &mdash; `MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS`:
  - Default (`True`): a relative link to a routed fixture `.md` file is
    rewritten to that route's URL, preserving any `#fragment`.
  - A relative link to an *unrouted* fixture `.md` file is left
    unchanged.
  - Absolute links, fully-qualified URLs, `mailto:`, and non-`.md`
    relative links are all left unchanged.
  - Setting `MARKDOWN_VIEW_REWRITE_INTERNAL_LINKS=False` disables
    rewriting entirely, even for a link that would otherwise resolve.

### `test_registry.py`

Focused, more granular coverage of `markdown_view/registry.py` directly
(not just through a rendered view), since it's the most logic-dense new
module:

- `resolve_markdown_source_path()` resolves a known `file_name` to the
  expected absolute path, and returns `None` for an unknown one.
- `build_markdown_view_url_registry()` / `_iter_markdown_view_routes()`
  correctly walk a nested/namespaced test urlconf and produce the
  expected `{path: url}` mapping, including through at least two levels
  of `include()` nesting.
- A registered route with **no `name=`** is skipped (can't reverse).
- A registered route with a required URL argument is skipped without
  raising (`NoReverseMatch` is caught).
- A route whose callback is **not** a `MarkdownView` subclass (e.g. a
  plain `TemplateView`) is skipped.
- `get_markdown_view_url_registry()` caching: confirm a second call
  without `force_refresh` reuses the cached dict (e.g. via identity
  check or a call-counting patch on `build_markdown_view_url_registry`),
  and that `force_refresh=True` rebuilds it.
- `clear_markdown_view_url_registry_cache()` actually clears the cache
  (next call rebuilds).
- `rewrite_markdown_links()` unit tests directly against small HTML
  snippets (not full rendered pages) for each of the link-shape cases
  listed in the fixture-file bullet above &mdash; this is faster to
  iterate on and pinpoints failures more precisely than only testing
  through the full view-rendering path.

### `test_loaders.py`

- `MarkdownLoader.get_dirs()` includes `BASE_DIR`/
  `MARKDOWN_VIEW_BASE_DIR` when set, and the app template dirs for
  `MARKDOWN_VIEW_LOADER_TEMPLATES_DIR`.
- `MarkdownLoader.get_template_sources()` yields exactly one `Origin` for
  a valid `"testapp/README.md"`-style name, yields nothing for a
  `file_name` not ending in `.md`, and does not raise (yields nothing)
  for a `file_name` whose resolved path would fall outside every
  candidate `template_dir` (the existing `SuspiciousFileOperation` guard).

### `test_markdown_extensions.py`

- `InlineImageProcessor`/`ImageExtension` in isolation (feed a small HTML
  tree, confirm `src` rewritten to `{% static %}` form and `class` set to
  `img-fluid`), independent of the full view pipeline.

### `test_settings_validation.py`

- Covers `markdown_view/__init__.py`'s `SETTINGS_TYPES` validation.
  Depends on resolving the import-time-validation testability tension
  flagged above; write these once that's settled.

### `test_checks.py`

- `markdown_view_check()` currently always returns `[]` (its one
  conditional branch is permanently `if False:`). At minimum, add a
  regression test asserting it returns `[]` given empty `app_configs`, so
  future changes to this function don't silently break the
  `Tags.security` check registration wired up in `apps.py`. If the dead
  `if False:` branch has no near-term purpose, consider removing it in
  this same pass (flag for the implementer's judgment; out of scope for
  a pure test-writing pass to decide unilaterally).

## Suggested CI matrix

Given `setup.py`'s declared support (`django>=2.2`) and current classifier
list (through Django 4 / Python 3.10), and that this branch's new code
runs fine under Django 5.2/Python 3.11 (per the `django-wrds` project's
own venv, used to develop and verify this feature), suggest trimming the
old exhaustive `tox.ini` matrix down to a realistic support window rather
than trying to preserve every historical entry, e.g.:

- Python: 3.9, 3.10, 3.11, 3.12
- Django: 4.2 (LTS), 5.0, 5.1 (or whatever the current stable/LTS set is
  at implementation time)
- One `pycodestyle` lint job (already present in `tox.ini`; keep it, but
  note current code under `markdown_view/registry.py` was written to
  Black-style ~88 columns, not strict PEP 8 79 columns like the rest of
  this package &mdash; reconcile the line-length convention project-wide
  during this pass, either by widening `pycodestyle`'s `max-line-length`
  or reflowing `registry.py`/the other recently-touched files to 79
  columns).

Replace `.travis.yml` with a GitHub Actions workflow
(`.github/workflows/test.yml`) running the above matrix via `tox`, plus a
`coveralls` upload step using `coveralls-python`'s GitHub Actions support
(no Travis-specific coveralls integration needed).

## Out of scope for this plan

- Actually writing the test code (deliberately left to the implementer /
  cloud agent, per this branch's purpose).
- Deciding the import-time-validation refactor for
  `markdown_view/__init__.py` outright &mdash; flagged as a design
  question above, not resolved here.
- Any behavior changes to `markdown_view/registry.py` or `views.py`
  itself; this plan is test-writing only. If gaps are found while writing
  tests, prefer opening them as follow-up issues rather than silently
  changing behavior on this branch.
