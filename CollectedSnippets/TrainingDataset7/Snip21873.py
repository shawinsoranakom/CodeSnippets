def test_listdir(self):
        """
        File storage returns a tuple containing directories and files.
        """
        self.assertFalse(self.storage.exists("storage_test_1"))
        self.assertFalse(self.storage.exists("storage_test_2"))
        self.assertFalse(self.storage.exists("storage_dir_1"))

        self.storage.save("storage_test_1", ContentFile("custom content"))
        self.storage.save("storage_test_2", ContentFile("custom content"))
        os.mkdir(os.path.join(self.temp_dir, "storage_dir_1"))

        self.addCleanup(self.storage.delete, "storage_test_1")
        self.addCleanup(self.storage.delete, "storage_test_2")

        for directory in ("", Path("")):
            with self.subTest(directory=directory):
                dirs, files = self.storage.listdir(directory)
                self.assertEqual(set(dirs), {"storage_dir_1"})
                self.assertEqual(set(files), {"storage_test_1", "storage_test_2"})