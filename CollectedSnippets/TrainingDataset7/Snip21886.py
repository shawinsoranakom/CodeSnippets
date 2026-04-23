def test_save_overwrite_behavior(self):
        """Saving to same file name twice overwrites the first file."""
        name = "test.file"
        self.assertFalse(self.storage.exists(name))
        content_1 = b"content one"
        content_2 = b"second content"
        f_1 = ContentFile(content_1)
        f_2 = ContentFile(content_2)
        stored_name_1 = self.storage.save(name, f_1)
        try:
            self.assertEqual(stored_name_1, name)
            self.assertTrue(self.storage.exists(name))
            with self.storage.open(name) as fp:
                self.assertEqual(fp.read(), content_1)
            stored_name_2 = self.storage.save(name, f_2)
            self.assertEqual(stored_name_2, name)
            self.assertTrue(self.storage.exists(name))
            with self.storage.open(name) as fp:
                self.assertEqual(fp.read(), content_2)
        finally:
            self.storage.delete(name)