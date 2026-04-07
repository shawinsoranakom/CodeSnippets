def test_json_multiple_access(self):
        response = self.client.get("/json_response/")
        self.assertIs(response.json(), response.json())