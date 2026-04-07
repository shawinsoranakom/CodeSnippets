def test_streaming_response(self):
        # Regression test for #5241
        response = self.client.get("/fr/streaming/")
        self.assertContains(response, "Oui/Non")
        response = self.client.get("/en/streaming/")
        self.assertContains(response, "Yes/No")