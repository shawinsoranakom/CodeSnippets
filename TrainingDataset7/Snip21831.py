def test_open_dir_as_file(self):
        with self.storage.open("a/b/file.txt", "w") as fd:
            fd.write("hello")
        self.assertRaises(IsADirectoryError, self.storage.open, "a/b")