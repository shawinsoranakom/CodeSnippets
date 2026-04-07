def test_filter_syntax18(self):
        """
        Strings are converted to bytestrings in the final output.
        """
        output = self.engine.render_to_string("filter-syntax18", {"var": UTF8Class()})
        self.assertEqual(output, "\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111")