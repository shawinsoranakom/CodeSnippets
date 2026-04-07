def test_find_partial_source_supports_nested_partials_and_mixed_end_tags_1(self):
        template = self.engine.get_template("nested_partials_mixed_end_1_template")

        empty_proxy = template.extra_data["partials"]["outer"]
        other_proxy = template.extra_data["partials"]["inner"]

        outer_result = empty_proxy.find_partial_source(template.source)
        self.assertEqual(
            outer_result,
            (
                "{% partialdef outer %}{% partialdef inner %}"
                "...{% endpartialdef %}{% endpartialdef outer %}"
            ),
        )

        inner_result = other_proxy.find_partial_source(template.source)
        self.assertEqual(inner_result, "{% partialdef inner %}...{% endpartialdef %}")