def test_quotes(self):
        self.assertEqual(
            escapejs_filter("\"double quotes\" and 'single quotes'"),
            "\\u0022double quotes\\u0022 and \\u0027single quotes\\u0027",
        )