"""
A view used only to manually explore this project's test fixtures (see
``markdown_view.tests.urls``), e.g. via ``python manage.py runserver``.
Not used by the automated test suite itself.
"""
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from markdown_view.registry import get_markdown_view_url_registry


def index(request):
    """
    A bare-bones index of every ``.md`` page currently routed via a
    ``MarkdownView`` (or subclass), each linked by its registered URL.

    Built from ``markdown_view.registry``'s URL registry -- the same one
    ``MarkdownView`` itself uses to rewrite inter-page links -- so this
    list always reflects whatever routes actually exist in ``urls.py``,
    rather than needing to be maintained (and kept in sync) by hand.
    """
    names = sorted(get_markdown_view_url_registry().values())
    items = format_html_join(
        "", "<li><a href=\"{}\">{}</a></li>",
        ((reverse(name), name) for name in names),
    )
    return HttpResponse(format_html(
        "<!DOCTYPE html>"
        "<html><head><title>markdown_view test pages</title></head>"
        "<body><h1>markdown_view test pages</h1><ul>{}</ul></body></html>",
        items,
    ))
