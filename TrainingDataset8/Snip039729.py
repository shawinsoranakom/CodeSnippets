def test_load_with_bad_path(self):
        """Adding a file by path raises a MediaFileStorageError if the file can't be read."""
        with self.assertRaises(MediaFileStorageError):
            self.storage.load_and_get_id(
                "mock/file/path",
                mimetype="video/mp4",
                kind=MediaFileKind.MEDIA,
                filename="file.mp4",
            )