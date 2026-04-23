def test_zero_if_file_nonexistent_and_allow_nonexistent(self):
        assert util.path_modification_time("foo", allow_nonexistent=True) == 0.0