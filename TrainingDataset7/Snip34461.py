def test_partial_template_embedded_in_named_verbatim(self):
        template = self.engine.get_template("partial_embedded_in_named_verbatim")
        partial_template = template.extra_data["partials"]["testing-name"]
        self.assertEqual(
            "{% partialdef testing-name %}\n<p>Named Content</p>\n{% endpartialdef %}",
            partial_template.source,
        )