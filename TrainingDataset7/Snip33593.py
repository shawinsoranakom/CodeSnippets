def test_filter_syntax16(self):
        """
        Escaped backslash using known escape char
        """
        output = self.engine.render_to_string("filter-syntax16", {"var": None})
        self.assertEqual(output, r"foo\now")