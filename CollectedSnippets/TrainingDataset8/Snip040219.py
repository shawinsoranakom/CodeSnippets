def test_stable_dir(self):
        assert util._stable_dir_identifier("my_dir", "*") == "my_dir+foo"