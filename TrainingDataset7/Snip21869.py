def test_save_doesnt_close(self):
        with TemporaryUploadedFile("test", "text/plain", 1, "utf8") as file:
            file.write(b"1")
            file.seek(0)
            self.assertFalse(file.closed)
            self.storage.save("path/to/test.file", file)
            self.assertFalse(file.closed)
            self.assertFalse(file.file.closed)

        file = InMemoryUploadedFile(StringIO("1"), "", "test", "text/plain", 1, "utf8")
        with file:
            self.assertFalse(file.closed)
            self.storage.save("path/to/test.file", file)
            self.assertFalse(file.closed)
            self.assertFalse(file.file.closed)