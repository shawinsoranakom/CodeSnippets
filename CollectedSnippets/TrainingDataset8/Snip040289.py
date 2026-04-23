def test_invalid_file(self) -> None:
        """Requests for invalid files fail with 404."""
        url = f"{MOCK_ENDPOINT}/invalid_media_file.mp4"
        rsp = self.fetch(url, method="GET")
        self.assertEqual(404, rsp.code)