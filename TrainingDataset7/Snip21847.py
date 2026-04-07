def test_file_created_time(self):
        """File creation time should not change after I/O operations."""
        self.storage.save("file.txt", ContentFile("test"))
        created_time = self.storage.get_created_time("file.txt")

        time.sleep(0.1)

        # File opening doesn't change creation time.
        file = self.storage.open("file.txt", "r")
        after_open_created_time = self.storage.get_created_time("file.txt")
        self.assertEqual(after_open_created_time, created_time)
        # Writing to a file doesn't change its creation time.
        file.write("New test")
        self.storage.save("file.txt", file)
        after_write_created_time = self.storage.get_created_time("file.txt")
        self.assertEqual(after_write_created_time, created_time)