def test_parsing_errors(self):
        with self.assertRaises(AssertionError):
            self.assertHTMLEqual("<p>", "")
        with self.assertRaises(AssertionError):
            self.assertHTMLEqual("", "<p>")
        error_msg = (
            "First argument is not valid HTML:\n"
            "('Unexpected end tag `div` (Line 1, Column 6)', (1, 6))"
        )
        with self.assertRaisesMessage(AssertionError, error_msg):
            self.assertHTMLEqual("< div></div>", "<div></div>")
        with self.assertRaises(HTMLParseError):
            parse_html("</p>")