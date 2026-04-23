def test_find_partial_source_multiple_consecutive_partials(self):
        template = self.engine.get_template("consecutive_partials_template")

        empty_proxy = template.extra_data["partials"]["empty"]
        other_proxy = template.extra_data["partials"]["other"]

        empty_result = empty_proxy.find_partial_source(template.source)
        self.assertEqual(empty_result, "{% partialdef empty %}{% endpartialdef %}")

        other_result = other_proxy.find_partial_source(template.source)
        self.assertEqual(other_result, "{% partialdef other %}...{% endpartialdef %}")