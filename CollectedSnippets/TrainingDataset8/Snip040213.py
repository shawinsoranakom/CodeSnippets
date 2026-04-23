def test_st_mtime_if_file_exists_and_allow_nonexistent(self):
        assert util.path_modification_time("foo", allow_nonexistent=True) == 101.0