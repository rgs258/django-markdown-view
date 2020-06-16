Django Markdown View
====================

**Serve .md pages as Django templates.**

.. contents:: Contents
    :depth: 5

.. note::
    * Tested with section describes aspirational goals.
    * Really, all directions describe aspirational goals.

Requirements
------------

Tested with:

* Python: 3.5, 3.6, 3.7, 3.8
* Django: 2.0, 2.1, 2.2, 3.0


.. note::
    * Django 2.2 requires SQLite 3.8.3
    * Django 2.2 supports Python 3.5, 3.6, and 3.7.
    * Django 3.0 supports Python 3.6, 3.7 and 3.8.

    We highly recommend and only officially support the latest release of each series.


Installation
------------

#. Install with ``pip install django-markdown-view``.

#. Add ``'markdown_view'`` to your ``INSTALLED_APPS`` setting.

    .. code-block:: python

        INSTALLED_APPS = [
            ...,
            'markdown_view',
            ...
        ]

#. (OPTIONAL) Add ``BASE_DIR`` setting (dictionary of app base), for example:

    .. code-block:: python

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


Usage
-----

Views
~~~~~~

Use one of ``MarkdownView``,  ``LoggedInMarkdownView``, or ``StaffMarkdownView``
to serve a .md file

.. code-block:: python

    from markdown_view import StaffMarkdownView

    path('readme/',
        StaffMarkdownView.as_view(file_name='my_app/README.md'),
        name="readme"),

