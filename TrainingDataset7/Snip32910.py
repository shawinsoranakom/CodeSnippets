def test_whitespace(self):
        self.assertEqual(
            escapejs_filter("and lots of whitespace: \r\n\t\v\f\b"),
            "and lots of whitespace: \\u000D\\u000A\\u0009\\u000B\\u000C\\u0008",
        )