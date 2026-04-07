def test_post(self):
        "Request a view via request method POST"
        response = self.client.post("/request_methods/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"request method: POST")