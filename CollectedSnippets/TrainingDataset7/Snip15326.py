def test_parse_rst_with_docstring_no_leading_line_feed(self):
        title, body, _ = parse_docstring("firstline\n\n    second line")
        with captured_stderr() as stderr:
            self.assertEqual(parse_rst(title, ""), "<p>firstline</p>\n")
            self.assertEqual(parse_rst(body, ""), "<p>second line</p>\n")
        self.assertEqual(stderr.getvalue(), "")