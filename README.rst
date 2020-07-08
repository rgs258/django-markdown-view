Django Markdown View
====================

**Serve .md pages as Django templates.**

.. contents:: Contents
    :depth: 5

.. note::
    * The Tested With section describes aspirational goals.
    * Really, all directions describe aspirational goals.

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
    The dictionary of the application's base. For example:

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
All settings are optional. See **markdown_view/constants.py** for the defaults.

* `MARKDOWN_VIEW_BASE_DIR` and `BASE_DIR`

    When present, the location to append to the list of dirs that Django's
    `django.template.utils.get_app_template_dirs` will return. Looks for
    `BASE_DIR` if `MARKDOWN_VIEW_BASE_DIR` is not found. This is used to
    allow .md files in the root of the project to be located.

* `MARKDOWN_VIEW_LOADERS`

    The loader that finds .md files in the context of any installed app or
    one of `MARKDOWN_VIEW_BASE_DIR` or `BASE_DIR`.

* `DEFAULT_MARKDOWN_VIEW_EXTENSIONS`

    The extensions to enable. See https://python-markdown.github.io/extensions/ and
    https://github.com/Python-Markdown/markdown/wiki/Third-Party-Extensions for more
    extensions. Note that `markdown_view.markdown_extensions.ImageExtension` is enabled
    and makes images responsive in bootstrap4. You can add you own extensions by
    following https://github.com/Python-Markdown/markdown/wiki/Tutorial-1---Writing-Extensions-for-Python-Markdown

* `DEFAULT_MARKDOWN_VIEW_TEMPLATE`

    The Django template that'll be used to render the HTML that is generated from the
    Markdown. Set your own template to style your pages. Context includes:

    * `markdown_content`: The HTML produced from the Markdown
    * `markdown_toc`: A table of contents from the headers of the Markdown
    * `page_title`: A guess at a page title, for now it's the first row of the TOC

Experimental Settings
~~~~~~~~~~~~~~~~~~~~~

* `DEFAULT_MARKDOWN_VIEW_USE_REQUEST_CONTEXT`

    If the request context should be used as a base when creating the context with
    which to render the Markdown internally. This is because the Markdown is rendered
    once first in order to prepend it with `{% load static %}`.
    This is not well tested; YMMV.

* `DEFAULT_MARKDOWN_VIEW_EXTRA_CONTEXT`

    Any extra context to send to the internal render of the Markdown. Can be used
    to expose context to template tags embedded in the Markdown.
    This is not well tested; YMMV.