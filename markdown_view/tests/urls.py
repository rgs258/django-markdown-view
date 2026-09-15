from django.urls import path

from markdown_view.views import MarkdownView

urlpatterns = [
    path(
        "readme/",
        MarkdownView.as_view(file_name="readme.md"),
        name="readme",
    ),
]
