def test_filter_syntax04(self):
        """
        Allow spaces after the filter pipe
        """
        output = self.engine.render_to_string(
            "filter-syntax04", {"var": "Django is the greatest!"}
        )
        self.assertEqual(output, "DJANGO IS THE GREATEST!")