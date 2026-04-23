def test_filter_syntax20(self):
        """
        Filters should accept empty string constants
        """
        output = self.engine.render_to_string("filter-syntax20")
        self.assertEqual(output, "")