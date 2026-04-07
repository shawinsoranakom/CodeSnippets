def test_save_overwrite_behavior_temp_file(self):
        """Saving to same file name twice overwrites the first file."""
        name = "test.file"
        self.assertFalse(self.storage.exists(name))
        content_1 = b"content one"
        content_2 = b"second content"
        f_1 = TemporaryUploadedFile("tmp1", "text/plain", 11, "utf8")
        self.addCleanup(f_1.close)
        f_1.write(content_1)
        f_1.seek(0)
        f_2 = TemporaryUploadedFile("tmp2", "text/plain", 14, "utf8")
        self.addCleanup(f_2.close)
        f_2.write(content_2)
        f_2.seek(0)
        stored_name_1 = self.storage.save(name, f_1)
        try:
            self.assertEqual(stored_name_1, name)
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, name)))
            with self.storage.open(name) as fp:
                self.assertEqual(fp.read(), content_1)
            stored_name_2 = self.storage.save(name, f_2)
            self.assertEqual(stored_name_2, name)
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, name)))
            with self.storage.open(name) as fp:
                self.assertEqual(fp.read(), content_2)
        finally:
            self.storage.delete(name)