def test_without_conditions(self):
        response = self.client.get("/condition/")
        self.assertFullResponse(response)