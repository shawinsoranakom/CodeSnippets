def test_filter_syntax01(self):
        """
        Basic filter usage
        """
        output = self.engine.render_to_string(
            "filter-syntax01", {"var": "Django is the greatest!"}
        )
        self.assertEqual(output, "DJANGO IS THE GREATEST!")