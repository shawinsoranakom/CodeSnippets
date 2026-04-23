def test_options(self):
        "Request a view via request method OPTIONS"
        response = self.client.options("/request_methods/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"request method: OPTIONS")