def test_json(self):
        response = self.client.get("/json_response/")
        self.assertEqual(response.json(), {"key": "value"})