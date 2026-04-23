def test_delete(self):
        """Deletion handles both files and directory trees."""
        self.storage.save("dir/subdir/file.txt", ContentFile("test"))
        self.storage.save("dir/subdir/other_file.txt", ContentFile("test"))
        self.assertTrue(self.storage.exists("dir/subdir/file.txt"))
        self.assertTrue(self.storage.exists("dir/subdir/other_file.txt"))

        self.storage.delete("dir/subdir/other_file.txt")
        self.assertFalse(self.storage.exists("dir/subdir/other_file.txt"))

        self.storage.delete("dir/subdir")
        self.assertFalse(self.storage.exists("dir/subdir/file.txt"))
        self.assertFalse(self.storage.exists("dir/subdir"))