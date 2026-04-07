def test_find_partial_source_empty_partial(self):
        template = self.engine.get_template("empty_partial_template")
        partial_proxy = template.extra_data["partials"]["empty"]

        result = partial_proxy.find_partial_source(template.source)
        self.assertEqual(result, "{% partialdef empty %}{% endpartialdef %}")