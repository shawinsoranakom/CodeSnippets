def test_clean_filename(self):
        """Test streamlit.string_util.clean_filename."""
        self.assertEqual("test_result", string_util.clean_filename("test re*su/lt;"))