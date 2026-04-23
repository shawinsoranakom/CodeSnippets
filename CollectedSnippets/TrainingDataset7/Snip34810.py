def test_head(self):
        "Request a view via request method HEAD"
        response = self.client.head("/request_methods/")
        self.assertEqual(response.status_code, 200)
        # A HEAD request doesn't return any content.
        self.assertNotEqual(response.content, b"request method: HEAD")
        self.assertEqual(response.content, b"")