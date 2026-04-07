def test_file_name_truncation(self):
        name = "test_long_file_name.txt"
        file = ContentFile(b"content")
        stored_name = self.storage.save(name, file, max_length=10)
        self.addCleanup(self.storage.delete, stored_name)
        self.assertEqual(stored_name, "test_l.txt")
        self.assertEqual(len(stored_name), 10)