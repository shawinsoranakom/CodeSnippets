def test_md5_calculation_opens_file_with_rb(self):
        # This tests implementation :( . But since the issue this is addressing
        # could easily come back to bite us if a distracted coder tweaks the
        # implementation, I'm putting this here anyway.
        with patch("streamlit.watcher.util.open", mock_open(read_data=b"hello")) as m:
            util.calc_md5_with_blocking_retries("foo")
            m.assert_called_once_with("foo", "rb")