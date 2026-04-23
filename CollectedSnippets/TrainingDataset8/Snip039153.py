def test_file_in_subfolder(self):
        # Test with and without trailing slash
        ret = file_util.file_is_in_folder_glob("/a/b/c/foo.py", "/a")
        self.assertTrue(ret)
        ret = file_util.file_is_in_folder_glob("/a/b/c/foo.py", "/a/")
        self.assertTrue(ret)
        ret = file_util.file_is_in_folder_glob("/a/b/c/foo.py", "/a/b")
        self.assertTrue(ret)
        ret = file_util.file_is_in_folder_glob("/a/b/c/foo.py", "/a/b/")
        self.assertTrue(ret)