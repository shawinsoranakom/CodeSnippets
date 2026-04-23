def test_nonexistent_path(self):
        with self.assertRaisesMessage(FileNotFoundError, "nonexistent"):
            FilePathField(path="nonexistent")