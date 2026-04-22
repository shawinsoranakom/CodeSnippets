def test_identical_files_have_same_id(self):
        """Two files with the same content, mimetype, and filename should share an ID."""
        # Create 2 identical files. We'll just get one ID.
        file_id1 = self.storage.load_and_get_id(
            b"mock_bytes",
            mimetype="video/mp4",
            kind=MediaFileKind.MEDIA,
            filename="file.mp4",
        )
        file_id2 = self.storage.load_and_get_id(
            b"mock_bytes",
            mimetype="video/mp4",
            kind=MediaFileKind.MEDIA,
            filename="file.mp4",
        )
        self.assertEqual(file_id1, file_id2)

        # Change file content -> different ID
        changed_content = self.storage.load_and_get_id(
            b"mock_bytes_2",
            mimetype="video/mp4",
            kind=MediaFileKind.MEDIA,
            filename="file.mp4",
        )
        self.assertNotEqual(file_id1, changed_content)

        # Change mimetype -> different ID
        changed_mimetype = self.storage.load_and_get_id(
            b"mock_bytes",
            mimetype="image/png",
            kind=MediaFileKind.MEDIA,
            filename="file.mp4",
        )
        self.assertNotEqual(file_id1, changed_mimetype)

        # Change (or omit) filename -> different ID
        changed_filename = self.storage.load_and_get_id(
            b"mock_bytes", mimetype="video/mp4", kind=MediaFileKind.MEDIA
        )
        self.assertNotEqual(file_id1, changed_filename)