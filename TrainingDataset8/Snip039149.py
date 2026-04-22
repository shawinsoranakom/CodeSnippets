def test_streamlit_write(self):
        """Test streamlitfile_util.streamlit_write."""

        dirname = os.path.dirname(file_util.get_streamlit_file_path(FILENAME))
        # patch streamlit.*.os.makedirs instead of os.makedirs for py35 compat
        with patch("streamlit.file_util.open", mock_open()) as open, patch(
            "streamlit.util.os.makedirs"
        ) as makedirs, file_util.streamlit_write(FILENAME) as output:
            output.write("some data")
            open().write.assert_called_once_with("some data")
            makedirs.assert_called_once_with(dirname, exist_ok=True)