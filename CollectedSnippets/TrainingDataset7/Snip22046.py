def test_extension_kept(self):
        """The temporary file name has the same suffix as the original file."""
        with TemporaryUploadedFile("test.txt", "text/plain", 1, "utf8") as temp_file:
            self.assertTrue(temp_file.file.name.endswith(".upload.txt"))