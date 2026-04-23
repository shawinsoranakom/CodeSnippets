def test_delete(self):
        "Request a view via request method DELETE"
        response = self.client.delete("/request_methods/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"request method: DELETE")