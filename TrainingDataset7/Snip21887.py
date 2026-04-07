def test_save_overwrite_behavior_truncate(self):
        name = "test.file"
        original_content = b"content extra extra extra"
        new_smaller_content = b"content"
        self.storage.save(name, ContentFile(original_content))
        try:
            self.storage.save(name, ContentFile(new_smaller_content))
            with self.storage.open(name) as fp:
                self.assertEqual(fp.read(), new_smaller_content)
        finally:
            self.storage.delete(name)