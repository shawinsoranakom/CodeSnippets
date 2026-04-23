def test_file_save_without_name(self):
        """
        File storage extracts the filename from the content object if no
        name is given explicitly.
        """
        self.assertFalse(self.storage.exists("test.file"))

        f = ContentFile("custom contents")
        f.name = "test.file"

        storage_f_name = self.storage.save(None, f)

        self.assertEqual(storage_f_name, f.name)

        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, f.name)))

        self.storage.delete(storage_f_name)