def test_streamlit_write_exception(self):
        """Test streamlitfile_util.streamlit_write."""
        with patch("streamlit.file_util.open", mock_open()) as p, patch(
            "streamlit.util.os.makedirs"
        ):
            p.side_effect = OSError(errno.EINVAL, "[Errno 22] Invalid argument")
            with pytest.raises(util.Error) as e, file_util.streamlit_write(
                FILENAME
            ) as output:
                output.write("some data")
            error_msg = (
                "Unable to write file: /some/cache/file\n"
                "Python is limited to files below 2GB on OSX. "
                "See https://bugs.python.org/issue24658"
            )
            self.assertEqual(str(e.value), error_msg)