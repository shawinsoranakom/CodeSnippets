def test_find_partial_source_success(self):
        template = self.engine.get_template("partial_source_success_template")
        partial_proxy = template.extra_data["partials"]["test-partial"]

        expected = """{% partialdef test-partial %}
TEST-PARTIAL-CONTENT
{% endpartialdef %}"""
        self.assertEqual(partial_proxy.source.strip(), expected.strip())