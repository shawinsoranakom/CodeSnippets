def test_filter_syntax10(self):
        """
        Literal string as argument is always "safe" from auto-escaping.
        """
        output = self.engine.render_to_string("filter-syntax10", {"var": None})
        self.assertEqual(output, ' endquote" hah')