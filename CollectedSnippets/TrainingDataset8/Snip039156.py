def test_file_in_folder_glob(self):
        ret = file_util.file_is_in_folder_glob("/a/b/c/foo.py", "**/c")
        self.assertTrue(ret)