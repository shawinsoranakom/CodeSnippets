def test_removing_temporary_file_after_save(self):
        """A temporary file is removed when saved into storage."""
        with TemporaryUploadedFile("test", "text/plain", 1, "utf8") as file:
            self.storage.save("test.txt", file)
            self.assertFalse(os.path.exists(file.temporary_file_path()))