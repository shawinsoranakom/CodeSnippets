def test_rel_file_not_in_folder_glob(self):
        ret = file_util.file_is_in_folder_glob("foo.py", "")
        self.assertTrue(ret)