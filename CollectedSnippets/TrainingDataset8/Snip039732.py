def test_delete_file(self):
        """delete_file removes the file with the given ID."""
        file_id1 = self.storage.load_and_get_id(
            b"mock_bytes_1",
            mimetype="video/mp4",
            kind=MediaFileKind.MEDIA,
            filename="file.mp4",
        )
        file_id2 = self.storage.load_and_get_id(
            b"mock_bytes_2",
            mimetype="video/mp4",
            kind=MediaFileKind.MEDIA,
            filename="file.mp4",
        )

        # delete file 1. It should not exist, but file2 should.
        self.storage.delete_file(file_id1)
        with self.assertRaises(Exception):
            self.storage.get_file(file_id1)

        self.assertIsNotNone(self.storage.get_file(file_id2))

        # delete file 2
        self.storage.delete_file(file_id2)
        with self.assertRaises(Exception):
            self.storage.get_file(file_id2)