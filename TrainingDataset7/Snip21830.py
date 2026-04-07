def test_open_missing_file(self):
        self.assertRaises(FileNotFoundError, self.storage.open, "missing.txt")