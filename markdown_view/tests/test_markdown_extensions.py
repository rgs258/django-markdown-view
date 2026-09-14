from xml.etree import ElementTree

import markdown
from django.test import SimpleTestCase

from markdown_view.markdown_extensions import ImageExtension, InlineImageProcessor


class InlineImageProcessorTests(SimpleTestCase):
    def _run(self, src):
        root = ElementTree.Element("div")
        img = ElementTree.SubElement(root, "img")
        img.set("src", src)
        InlineImageProcessor(md=None).run(root)
        return root.find("img")

    def test_rewrites_src_to_static_tag(self):
        img = self._run("foo.png")
        self.assertEqual(img.attrib["src"], "{% static 'foo.png' %}")

    def test_strips_leading_static_segment(self):
        img = self._run("/static/images/foo.png")
        self.assertEqual(img.attrib["src"], "{% static 'images/foo.png' %}")

    def test_sets_img_fluid_class(self):
        img = self._run("foo.png")
        self.assertEqual(img.attrib["class"], "img-fluid")


class ImageExtensionTests(SimpleTestCase):
    def test_extends_markdown_conversion(self):
        md = markdown.Markdown(extensions=[ImageExtension()])
        html = md.convert("![alt text](foo.png)")
        self.assertIn("{% static 'foo.png' %}", html)
        self.assertIn('class="img-fluid"', html)
        self.assertIn('alt="alt text"', html)
