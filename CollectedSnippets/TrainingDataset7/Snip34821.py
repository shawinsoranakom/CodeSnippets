def test_json_charset(self):
        response = self.client.get("/json_response_latin1/")
        self.assertEqual(response.charset, "latin1")
        self.assertEqual(response.json(), {"a": "Å"})