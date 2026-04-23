def test_file_not_in_folder(self):
        # Test with and without trailing slash
        ret = file_util.file_is_in_folder_glob("/a/b/c/foo.py", "/d/e/f/")
        self.assertFalse(ret)
        ret = file_util.file_is_in_folder_glob("/a/b/c/foo.py", "/d/e/f")
        self.assertFalse(ret)