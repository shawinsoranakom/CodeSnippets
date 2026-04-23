def test_read_numbytes_from_nonempty_request(self):
        """HttpRequest.read(LARGE_BUFFER) on a test client PUT request with
        some payload should return that payload."""
        payload = b"foobar"
        self.assertEqual(
            self.client.put(
                "/read_buffer/", data=payload, content_type="text/plain"
            ).content,
            payload,
        )