def test_filter_syntax03(self):
        """
        Allow spaces before the filter pipe
        """
        output = self.engine.render_to_string(
            "filter-syntax03", {"var": "Django is the greatest!"}
        )
        self.assertEqual(output, "DJANGO IS THE GREATEST!")