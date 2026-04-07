def test_file_modified_time(self):
        """
        File modified time should change after file changing
        """
        self.storage.save("file.txt", ContentFile("test"))
        modified_time = self.storage.get_modified_time("file.txt")

        time.sleep(0.1)

        with self.storage.open("file.txt", "w") as fd:
            fd.write("new content")

        new_modified_time = self.storage.get_modified_time("file.txt")
        self.assertTrue(new_modified_time > modified_time)