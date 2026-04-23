def test_directory_times_changing_after_file_deletion(self):
        """
        Directory modified and accessed time should change when a new file is
        deleted inside.
        """
        self.storage.save("dir/file.txt", ContentFile("test"))
        created_time = self.storage.get_created_time("dir")
        modified_time = self.storage.get_modified_time("dir")
        accessed_time = self.storage.get_accessed_time("dir")

        time.sleep(0.1)

        self.storage.delete("dir/file.txt")
        new_modified_time = self.storage.get_modified_time("dir")
        new_accessed_time = self.storage.get_accessed_time("dir")
        after_file_deletion_created_time = self.storage.get_created_time("dir")
        self.assertGreater(new_modified_time, modified_time)
        self.assertGreater(new_accessed_time, accessed_time)
        self.assertEqual(created_time, after_file_deletion_created_time)