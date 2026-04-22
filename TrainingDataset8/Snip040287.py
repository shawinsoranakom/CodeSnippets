def test_media_file(self) -> None:
        """Requests for media files in MediaFileManager should succeed."""
        # Add a media file and read it back
        url = self.media_file_manager.add(b"mock_data", "video/mp4", "mock_coords")
        rsp = self.fetch(url, method="GET")

        self.assertEqual(200, rsp.code)
        self.assertEqual(b"mock_data", rsp.body)
        self.assertEqual("video/mp4", rsp.headers["Content-Type"])
        self.assertEqual(str(len(b"mock_data")), rsp.headers["Content-Length"])