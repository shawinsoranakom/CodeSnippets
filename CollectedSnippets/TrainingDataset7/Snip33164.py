def test_invalid_arg(self):
        self.assertEqual(truncatewords_html("<p>string</p>", "a"), "<p>string</p>")