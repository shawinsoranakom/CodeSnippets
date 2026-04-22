def test_file_not_in_folder_glob(self):
        ret = file_util.file_is_in_folder_glob("/a/b/c/foo.py", "**/f")
        self.assertFalse(ret)