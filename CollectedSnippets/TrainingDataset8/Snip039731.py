def test_get_url_invalid_fileid(self):
        """get_url raises if it gets a bad file_id."""
        with self.assertRaises(MediaFileStorageError):
            self.storage.get_url("not_a_file_id")