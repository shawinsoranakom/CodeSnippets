def test_filter_syntax02(self):
        """
        Chained filters
        """
        output = self.engine.render_to_string(
            "filter-syntax02", {"var": "Django is the greatest!"}
        )
        self.assertEqual(output, "django is the greatest!")