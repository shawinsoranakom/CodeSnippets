def test_read_from_empty_request(self):
        """HttpRequest.read() on a test client GET request should return the
        empty string."""
        self.assertEqual(self.client.get("/read_all/").content, b"")