def test_custom_storage_discarding_empty_content(self):
        """
        When Storage.save() wraps a file-like object in File, it should include
        the name argument so that bool(file) evaluates to True (#26495).
        """
        output = StringIO("content")
        self.storage.save("tests/stringio", output)
        self.assertTrue(self.storage.exists("tests/stringio"))

        with self.storage.open("tests/stringio") as f:
            self.assertEqual(f.read(), b"content")