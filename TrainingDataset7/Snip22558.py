def test_filefield_3(self):
        f = FileField(allow_empty_file=True)
        self.assertIsInstance(
            f.clean(SimpleUploadedFile("name", b"")), SimpleUploadedFile
        )