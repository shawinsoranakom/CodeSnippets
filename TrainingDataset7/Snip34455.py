def test_find_partial_source_supports_nested_partials(self):
        template = self.engine.get_template("nested_partials_basic_template")

        empty_proxy = template.extra_data["partials"]["outer"]
        other_proxy = template.extra_data["partials"]["inner"]

        outer_result = empty_proxy.find_partial_source(template.source)
        self.assertEqual(
            outer_result,
            (
                "{% partialdef outer %}{% partialdef inner %}"
                "...{% endpartialdef %}{% endpartialdef %}"
            ),
        )

        inner_result = other_proxy.find_partial_source(template.source)
        self.assertEqual(inner_result, "{% partialdef inner %}...{% endpartialdef %}")