def test_file_accessed_time(self):
        """File accessed time should change after consecutive opening."""
        self.storage.save("file.txt", ContentFile("test"))
        accessed_time = self.storage.get_accessed_time("file.txt")

        time.sleep(0.1)

        self.storage.open("file.txt", "r")
        new_accessed_time = self.storage.get_accessed_time("file.txt")
        self.assertGreater(new_accessed_time, accessed_time)