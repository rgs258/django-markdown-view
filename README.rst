Django Markdown View
====================

.. image:: https://travis-ci.org/rgs258/django-markdown-view.svg?branch=master
    :target: https://travis-ci.org/rgs258/django-markdown-view

.. image:: https://coveralls.io/repos/github/rgs258/django-markdown-view/badge.svg?branch=master
    :target: https://coveralls.io/github/rgs258/django-markdown-view?branch=master


**Serve .md pages as Django views.**

This package aims to make it easy to serve .md files on Django sites.


.. contents:: Contents
    :depth: 5

.. note::
    * This package needs tests, and to have Travis and Coveralls properly configured.

Requirements
------------

Tested with:

**The Tested With section describes aspirational goals.**

* Python: 3.5, 3.6, 3.7, 3.8
* Django: 2.2, 3.0


.. note::
    * Django 2.2 requires SQLite 3.8.3
    * Django 2.2 supports Python 3.5, 3.6, and 3.7.
    * Django 3.0 supports Python 3.6, 3.7 and 3.8.

    We highly recommend and only officially support the latest release of each series.


Installation
------------

#. Install with ``pip install django-markdown-view``.

#. Add ``'markdown_view'`` to your ``INSTALLED_APPS`` settings.

    .. code-block:: python

        INSTALLED_APPS = [
            ...,
            'markdown_view',
            ...
        ]

#. (OPTIONAL) Add ``MARKDOWN_VIEW_BASE_DIR`` or ``BASE_DIR`` to settings
    The dictionary of the application's base. See Settings_ below

    For example, if settings are in config/settings/base.py, then:

    .. code-block:: python

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


Usage
-----

Views
~~~~~

Use one of ``MarkdownView``,  ``LoggedInMarkdownView``, or ``StaffMarkdownView``
from ``markdown_view.views`` to serve a .md file

.. code-block:: python

    from markdown_view.views import StaffMarkdownView

    path('readme/',
        StaffMarkdownView.as_view(file_name='my_app/README.md'),
        name="readme"),


Settings
~~~~~~~~
All settings are optional. See `<markdown_view/constants.py>`_ for the defaults.

* `MARKDOWN_VIEW_BASE_DIR` and `BASE_DIR`

    When present, the value is taken as a location to append to the list of dirs that
    Django's `django.template.utils.get_app_template_dirs` will return when passed
    `dirname=""`. This is used to locate .md files in the root of the project, e.g.,
    a README.md file. Looks for `BASE_DIR` if `MARKDOWN_VIEW_BASE_DIR` is not found.

* `MARKDOWN_VIEW_LOADERS`

    A list of loaders that locate .md files. The default list includes only
    `markdown_view.loaders.MarkdownLoader` which will by default try to load .md files
    from root directories in INSTALLED_APPS packages much the same as Django's
    `django.template.loaders.app_directories.Loader` looks to load from "templates".

* `MARKDOWN_VIEW_LOADER_TEMPLATES_DIR`

    The name of the directories in INSTALLED_APPS packages in which to locate .md
    files. Defaults to "" in order to locate .md filed in the root directories.

* `MARKDOWN_VIEW_EXTENSIONS`

    The extensions to enable. These extensions are enabled be default:

    * `toc`:
        generates a Table of Contents. If `toc` is removed from extensions, then
        `MARKDOWN_VIEW_TEMPLATE_USE_TOC` must be set to False.

    * `tables`:
        enables tables.

    * `fenced_code`:
        enables code blocks. If `fenced_code` is removed from extensions, then
        `MARKDOWN_VIEW_TEMPLATE_USE_HIGHLIGHT_JS`, which provides the highlighting for
        code blocks, can be disabled.

    * `markdown_view.markdown_extensions.ImageExtension`:
        makes images responsive in bootstrap4.

    See https://python-markdown.github.io/extensions/ and
    https://github.com/Python-Markdown/markdown/wiki/Third-Party-Extensions for more
    extensions.

    You can create your own extensions by following
    https://github.com/Python-Markdown/markdown/wiki/Tutorial-1---Writing-Extensions-for-Python-Markdown

* `MARKDOWN_VIEW_TEMPLATE`

    The Django template that'll be used to render the HTML that is generated from the
    Markdown. Set your own template to style your pages. Context includes:

    * `markdown_content`:
        The HTML produced from the Markdown.

    * `use_highlight_js`:
        If highlight.js is enabled.

    * `use_toc`:
        If the table of contents should be rendered.

    * `markdown_toc`:
        A table of contents from the headers of the Markdown. Not set when `use_toc`
        is False.

    * `page_title`:
        A guess at a page title, for now it's the first row of the TOC. Not set when
        `use_toc` is False.

* `MARKDOWN_VIEW_TEMPLATE_USE_TOC`

    Whether to render the TOC. If false, in the template context, `use_toc` is False
    and `markdown_toc` and `page_title` are not present.

* `MARKDOWN_VIEW_TEMPLATE_USE_HIGHLIGHT_JS`

    Whether to load and activate the highlight.js library in the template.

Experimental Settings
~~~~~~~~~~~~~~~~~~~~~

* `MARKDOWN_VIEW_USE_REQUEST_CONTEXT`

    If the request context should be used as a base when creating the context with
    which to render the Markdown internally. This is because the Markdown is rendered
    once first in order to prepend it with `{% load static %}`.
    This is not well tested; YMMV.

* `MARKDOWN_VIEW_EXTRA_CONTEXT`

    Any extra context to send to the internal render of the Markdown. Can be used
    to expose context to template tags embedded in the Markdown.
    This is not well tested; YMMV.


Implementation
--------------

At a high level, `MarkdownView` will:

#. Use a template loader to locate .md given as `file_name`

#. Render as a template, the contents of the .md file prepended with
   `{{% load static %}}`, into several context variables

#. Serve the `MARKDOWN_VIEW_TEMPLATE` with the context variables


Contributing
------------

All contributions are very welcomed. Propositions, problems, bugs, and
enhancement are tracked with `GitHub issues`_ and patches are submitted
via `pull requests`_.

We use `Travis`_ coupled with `Coveralls`_ as continious integration tools.

.. _`GitHub issues`: https://github.com/rgs258/django-markdown-view/issues
.. _`pull requests`: https://github.com/rgs258/django-markdown-view/pulls
.. _Travis: https://travis-ci.org/github/rgs258/django-markdown-view
.. _Coveralls: https://coveralls.io/github/rgs258/django-markdown-view
