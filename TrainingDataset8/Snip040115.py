def test_decode_ascii(self):
        """Test streamlit.string_util.decode_ascii."""
        self.assertEqual("test string.", string_util.decode_ascii(b"test string."))