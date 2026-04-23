def test_file_save_with_path(self):
        """
        Saving a pathname should create intermediate directories as necessary.
        """
        self.assertFalse(self.storage.exists("path/to"))
        self.storage.save("path/to/test.file", ContentFile("file saved with path"))

        self.assertTrue(self.storage.exists("path/to"))
        with self.storage.open("path/to/test.file") as f:
            self.assertEqual(f.read(), b"file saved with path")

        self.assertTrue(
            os.path.exists(os.path.join(self.temp_dir, "path", "to", "test.file"))
        )

        self.storage.delete("path/to/test.file")