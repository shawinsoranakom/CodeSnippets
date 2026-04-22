def test_delete_invalid_file_is_a_noop(self):
        """deleting a file that doesn't exist doesn't raise an error."""
        self.storage.delete_file("mock_file_id")