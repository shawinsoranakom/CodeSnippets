def test_stable_dir_files_change(self):
        assert util._stable_dir_identifier("my_dir", "*") == "my_dir+bar"