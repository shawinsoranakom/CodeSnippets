def test_is_emoji(self, text: str, expected: bool):
        """Test streamlit.string_util.is_emoji."""
        self.assertEqual(string_util.is_emoji(text), expected)