import re

from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension


class InlineImageProcessor(Treeprocessor):
    def run(self, root):
        for element in root.iter("img"):
            src_orig = element.attrib.get('src', '')
            src_re = re.sub("[/\\\]*static[/\\\]*", "", src_orig)
            src = "{{% static '{}' %}}".format(src_re)
            element.attrib["src"] = src
            element.attrib["class"] = "img-fluid"


class ImageExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(InlineImageProcessor(md), 'inlineimageprocessor', 15)
