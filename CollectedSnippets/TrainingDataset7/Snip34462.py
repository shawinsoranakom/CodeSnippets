def test_partial_template_embedded_in_comment_block(self):
        template = self.engine.get_template("partial_embedded_in_comment_block")
        partial_template = template.extra_data["partials"]["testing-name"]
        self.assertEqual(
            partial_template.source,
            "{% partialdef testing-name %}\n"
            "<p>Comment Content</p>\n"
            "{% endpartialdef %}",
        )