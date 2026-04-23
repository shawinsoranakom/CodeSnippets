def test_delete_missing_file(self):
        self.storage.delete("missing_file.txt")
        self.storage.delete("missing_dir/missing_file.txt")