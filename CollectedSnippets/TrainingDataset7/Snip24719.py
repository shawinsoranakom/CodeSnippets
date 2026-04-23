def test_no_transaction(self):
        response = self.client.get("/in_transaction/")
        self.assertContains(response, "False")