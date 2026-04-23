def test_body_from_empty_request(self):
        """HttpRequest.body on a test client GET request should return
        the empty string."""
        self.assertEqual(self.client.get("/body/").content, b"")