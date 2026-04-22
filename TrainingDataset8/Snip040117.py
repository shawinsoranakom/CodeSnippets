def test_extract_leading_emoji(self, text, expected):
        self.assertEqual(string_util.extract_leading_emoji(text), expected)