def test_file_name_truncation_extension_too_long(self):
        name = "file_name.longext"
        file = ContentFile(b"content")
        with self.assertRaisesMessage(
            SuspiciousFileOperation, "Storage can not find an available filename"
        ):
            self.storage.save(name, file, max_length=5)