def test_st_mtime_if_file_exists(self):
        assert util.path_modification_time("foo") == 101.0