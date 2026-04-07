def test_exists(self):
        self.storage.save("dir/subdir/file.txt", ContentFile("test"))
        self.assertTrue(self.storage.exists("dir"))
        self.assertTrue(self.storage.exists("dir/subdir"))
        self.assertTrue(self.storage.exists("dir/subdir/file.txt"))