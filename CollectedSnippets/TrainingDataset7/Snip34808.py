def test_get(self):
        "Request a view via request method GET"
        response = self.client.get("/request_methods/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"request method: GET")