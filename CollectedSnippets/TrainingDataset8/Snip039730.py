def test_get_url(self, mimetype, extension):
        """URLs should be formatted correctly, and have the expected extension."""
        file_id = self.storage.load_and_get_id(
            b"mock_bytes", mimetype=mimetype, kind=MediaFileKind.MEDIA
        )
        url = self.storage.get_url(file_id)
        self.assertEqual(f"/mock/media/{file_id}{extension}", url)