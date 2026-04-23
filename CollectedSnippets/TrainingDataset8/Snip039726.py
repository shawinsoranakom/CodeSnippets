def test_load_with_path(self):
        """Adding a file by path creates a MemoryFile instance."""
        file_id = self.storage.load_and_get_id(
            "mock/file/path",
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