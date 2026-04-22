def test_streamlit_read_binary(self):
        """Test streamlitfile_util.streamlit_read."""
        with file_util.streamlit_read(FILENAME, binary=True) as input:
            data = input.read()
        self.assertEqual(b"\xaa\xbb", data)