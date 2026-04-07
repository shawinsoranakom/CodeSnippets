def test_filter_syntax15(self):
        """
        Escaped backslash in argument
        """
        output = self.engine.render_to_string("filter-syntax15", {"var": None})
        self.assertEqual(output, r"foo\bar")