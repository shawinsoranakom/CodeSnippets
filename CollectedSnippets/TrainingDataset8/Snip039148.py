def test_streamlit_read_zero_bytes(self):
        """Test streamlitfile_util.streamlit_read."""
        self.os_stat.return_value.st_size = 0
        with pytest.raises(util.Error) as e:
            with file_util.streamlit_read(FILENAME) as input:
                input.read()
        self.assertEqual(str(e.value), 'Read zero byte file: "/some/cache/file"')