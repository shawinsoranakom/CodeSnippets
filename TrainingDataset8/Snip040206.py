def test_md5_calculation_succeeds_with_bytes_input(self):
        with patch("streamlit.watcher.util.open", mock_open(read_data=b"hello")) as m:
            md5 = util.calc_md5_with_blocking_retries("foo")
            self.assertEqual(md5, "5d41402abc4b2a76b9719d911017c592")