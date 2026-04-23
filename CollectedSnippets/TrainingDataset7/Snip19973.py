def test_different_nonce_per_request(self):
        response1 = self.client.get("/csp_nonce/")
        response2 = self.client.get("/csp_nonce/")
        self.assertNotEqual(
            response1.context["csp_nonce"],
            response2.context["csp_nonce"],
        )