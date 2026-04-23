def test_content_file_default_name(self):
        self.assertIsNone(ContentFile(b"content").name)