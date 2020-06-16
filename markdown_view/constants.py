from markdown_view.markdown_extensions import ImageExtension

DEFAULT_MARKDOWN_VIEW_LOADERS = ["markdown_view.loaders.MarkdownLoader", ]
DEFAULT_MARKDOWN_VIEW_EXTENSIONS = ["tables", "fenced_code", "toc", ImageExtension(), ]
DEFAULT_MARKDOWN_VIEW_TEMPLATE = "markdown_view/markdown.html"
DEFAULT_MARKDOWN_VIEW_USE_REQUEST_CONTEXT = False
DEFAULT_MARKDOWN_VIEW_EXTRA_CONTEXT = {}
