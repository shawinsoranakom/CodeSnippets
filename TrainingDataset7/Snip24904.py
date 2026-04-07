def test_no_prefix_response(self):
        response = self.client.get("/not-prefixed/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Vary"), "Accept-Language")