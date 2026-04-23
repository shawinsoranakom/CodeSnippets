def test_put(self):
        "Request a view via request method PUT"
        response = self.client.put("/request_methods/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"request method: PUT")