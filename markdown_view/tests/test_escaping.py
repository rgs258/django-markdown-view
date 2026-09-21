from django.test import SimpleTestCase

from markdown_view.escaping import escape_unsafe_template_syntax


class EscapeUnsafeTemplateSyntaxTests(SimpleTestCase):
    def test_static_tag_left_unescaped(self):
        html = "<img src=\"{% static 'image.png' %}\">"
        result = escape_unsafe_template_syntax(html)
        self.assertEqual(result, html)

    def test_safe_variable_left_unescaped(self):
        html = "<p>pk is {{ pk }}</p>"
        result = escape_unsafe_template_syntax(html, safe_context_keys={"pk"})
        self.assertEqual(result, html)

    def test_variable_not_in_safe_keys_is_escaped(self):
        html = "<p>value is {{ some_variable }}</p>"
        result = escape_unsafe_template_syntax(html, safe_context_keys=set())
        self.assertEqual(result, "<p>value is &#123;&#123; some_variable &#125;&#125;</p>")

    def test_variable_with_no_safe_keys_provided_is_escaped(self):
        html = "<p>value is {{ some_variable }}</p>"
        result = escape_unsafe_template_syntax(html)
        self.assertEqual(result, "<p>value is &#123;&#123; some_variable &#125;&#125;</p>")

    def test_arbitrary_block_tag_is_escaped(self):
        html = "<p>{% include 'whatever.html' %}</p>"
        result = escape_unsafe_template_syntax(html)
        self.assertEqual(
            result, "<p>&#123;% include 'whatever.html' %&#125;</p>"
        )

    def test_dotted_or_filtered_variable_is_escaped_even_if_name_matches(self):
        # Only bare `{{ identifier }}` is treated as safe -- anything with
        # a dotted lookup or filter is prose, not a real reference, even
        # if the leading name happens to match a safe key.
        html = "<p>{{ pk.something }} and {{ pk|upper }}</p>"
        result = escape_unsafe_template_syntax(html, safe_context_keys={"pk"})
        self.assertEqual(
            result,
            "<p>&#123;&#123; pk.something &#125;&#125; and "
            "&#123;&#123; pk|upper &#125;&#125;</p>",
        )

    def test_static_tag_with_different_path_still_matches(self):
        html = "{% static 'css/some-file.css' %}"
        result = escape_unsafe_template_syntax(html)
        self.assertEqual(result, html)

    def test_non_static_block_tag_matching_similar_shape_is_escaped(self):
        # Only the exact `{% static '...' %}` shape is trusted -- a
        # same-looking but different tag name must not slip through.
        html = "{% statictag 'whatever' %}"
        result = escape_unsafe_template_syntax(html)
        self.assertEqual(result, "&#123;% statictag 'whatever' %&#125;")

    def test_plain_text_without_any_template_syntax_is_unchanged(self):
        html = "<p>Nothing template-shaped here.</p>"
        result = escape_unsafe_template_syntax(html)
        self.assertEqual(result, html)

    def test_multiple_spans_on_different_lines_handled_independently(self):
        html = (
            "<p>{% static 'a.png' %}</p>\n"
            "<p>{{ unsafe_variable }}</p>\n"
            "<p>{{ pk }}</p>"
        )
        result = escape_unsafe_template_syntax(html, safe_context_keys={"pk"})
        self.assertEqual(
            result,
            "<p>{% static 'a.png' %}</p>\n"
            "<p>&#123;&#123; unsafe_variable &#125;&#125;</p>\n"
            "<p>{{ pk }}</p>",
        )
