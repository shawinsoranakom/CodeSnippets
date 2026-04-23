def test_escaped_html_errors(self):
        msg = "<p>\n<foo>\n</p> != <p>\n&lt;foo&gt;\n</p>\n"
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertHTMLEqual("<p><foo></p>", "<p>&lt;foo&gt;</p>")
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertHTMLEqual("<p><foo></p>", "<p>&#60;foo&#62;</p>")