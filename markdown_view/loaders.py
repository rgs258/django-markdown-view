from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.template import Origin
from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.template.utils import get_app_template_dirs
from django.utils._os import safe_join

from markdown_view.constants import DEFAULT_MARKDOWN_VIEW_LOADER_TEMPLATES_DIR


class MarkdownLoader(FilesystemLoader):
    """
    A loader that will find a .md file in the context of any installed app or
    application root.
    """

    def get_dirs(self):
        base_dir = getattr(
            settings,
            "MARKDOWN_VIEW_BASE_DIR",
            getattr(
                settings,
                "BASE_DIR",
                None)
        )
        dirs = [*get_app_template_dirs(
            getattr(
                settings,
                "MARKDOWN_VIEW_LOADER_TEMPLATES_DIR",
                DEFAULT_MARKDOWN_VIEW_LOADER_TEMPLATES_DIR
            )
        )]
        if base_dir:
            dirs.extend([base_dir])
        return dirs

    def get_template_sources(self, template_name):
        """
        Return an Origin object pointing to an absolute path in each directory
        in template_dirs. For security reasons, if a path doesn't lie inside
        one of the template_dirs it is excluded from the result set.
        """
        if template_name.endswith('.md'):
            template_split = template_name.split("/")
            template_split.reverse()
            template_app_dir = template_split.pop()
            template_split.reverse()
            for template_dir in self.get_dirs():
                if template_dir.endswith(template_app_dir):
                    try:
                        name = safe_join(template_dir, *template_split)
                    except SuspiciousFileOperation:
                        # The joined path was located outside of this template_dir
                        # (it might be inside another one, so this isn't fatal).
                        continue

                    yield Origin(
                        name=name,
                        template_name=template_name,
                        loader=self,
                    )
