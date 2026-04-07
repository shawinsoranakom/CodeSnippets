def test_csp_nonce_in_context(self):
        response = self.client.get("/csp_nonce/")
        self.assertIn("csp_nonce", response.context)