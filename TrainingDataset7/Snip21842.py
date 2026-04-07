def test_url(self):
        self.assertRaises(ValueError, self.storage.url, ("file.txt",))

        storage = InMemoryStorage(base_url="http://www.example.com")
        self.assertEqual(storage.url("file.txt"), "http://www.example.com/file.txt")