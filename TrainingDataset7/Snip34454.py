def test_find_partial_source_supports_named_end_tag(self):
        template = self.engine.get_template("named_end_tag_template")
        partial_proxy = template.extra_data["partials"]["thing"]

        result = partial_proxy.find_partial_source(template.source)
        self.assertEqual(
            result, "{% partialdef thing %}CONTENT{% endpartialdef thing %}"
        )