def test_read_numbytes_from_empty_request(self):
        """HttpRequest.read(LARGE_BUFFER) on a test client GET request should
        return the empty string."""
        self.assertEqual(self.client.get("/read_buffer/").content, b"")