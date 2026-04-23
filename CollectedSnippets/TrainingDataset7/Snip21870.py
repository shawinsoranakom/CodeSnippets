def test_file_path(self):
        """
        File storage returns the full path of a file
        """
        self.assertFalse(self.storage.exists("test.file"))

        f = ContentFile("custom contents")
        f_name = self.storage.save("test.file", f)

        self.assertEqual(self.storage.path(f_name), os.path.join(self.temp_dir, f_name))

        self.storage.delete(f_name)