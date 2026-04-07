def test_patch(self):
        "Request a view via request method PATCH"
        response = self.client.patch("/request_methods/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"request method: PATCH")