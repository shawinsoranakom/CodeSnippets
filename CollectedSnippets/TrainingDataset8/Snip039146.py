def test_streamlit_read(self):
        """Test streamlitfile_util.streamlit_read."""
        with file_util.streamlit_read(FILENAME) as input:
            data = input.read()
        self.assertEqual("data", data)