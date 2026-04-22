def test_load_with_bytes(self):
        """Adding a file with bytes creates a MemoryFile instance."""
        file_id = self.storage.load_and_get_id(
            b"mock_bytes",
            mimetype="video/mp4",
            kind=MediaFileKind.MEDIA,
            filename="file.mp4",
        )
        self.assertEqual(
            MemoryFile(
                content=b"mock_bytes",
                mimetype="video/mp4",
                kind=MediaFileKind.MEDIA,
                filename="file.mp4",
            ),
            self.storage.get_file(file_id),
        )