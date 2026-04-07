def test_file_storage_prevents_directory_traversal(self):
        """
        File storage prevents directory traversal (files can only be accessed
        if they're below the storage location).
        """
        with self.assertRaises(SuspiciousFileOperation):
            self.storage.exists("..")
        with self.assertRaises(SuspiciousFileOperation):
            self.storage.exists("/etc/passwd")