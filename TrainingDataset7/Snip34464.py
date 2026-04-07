def test_partial_template_contains_fake_end_inside_verbatim(self):
        template = self.engine.get_template("partial_contains_fake_end_inside_verbatim")
        partial_template = template.extra_data["partials"]["testing-name"]
        self.assertEqual(
            partial_template.source,
            "{% partialdef testing-name %}\n"
            "{% verbatim %}{% endpartialdef %}{% endverbatim %}\n"
            "<p>Body</p>\n"
            "{% endpartialdef %}",
        )