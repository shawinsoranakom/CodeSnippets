def test_read_from_nonempty_request(self):
        """HttpRequest.read() on a test client PUT request with some payload
        should return that payload."""
        payload = b"foobar"
        self.assertEqual(
            self.client.put(
                "/read_all/", data=payload, content_type="text/plain"
            ).content,
            payload,
        )