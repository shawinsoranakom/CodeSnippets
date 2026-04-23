def test_file_access_options(self):
        """
        Standard file access options are available, and work as expected.
        """
        self.assertFalse(self.storage.exists("storage_test"))
        f = self.storage.open("storage_test", "w")
        f.write("storage contents")
        f.close()
        self.assertTrue(self.storage.exists("storage_test"))

        f = self.storage.open("storage_test", "r")
        self.assertEqual(f.read(), "storage contents")
        f.close()

        self.storage.delete("storage_test")
        self.assertFalse(self.storage.exists("storage_test"))