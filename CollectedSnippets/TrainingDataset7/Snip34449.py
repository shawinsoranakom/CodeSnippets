def test_find_partial_source_with_inline(self):
        template = self.engine.get_template("partial_source_with_inline_template")
        partial_proxy = template.extra_data["partials"]["inline-partial"]

        expected = """{% partialdef inline-partial inline %}
INLINE-CONTENT
{% endpartialdef %}"""
        self.assertEqual(partial_proxy.source.strip(), expected.strip())