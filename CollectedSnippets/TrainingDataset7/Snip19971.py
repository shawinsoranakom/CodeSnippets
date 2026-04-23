def test_csp_nonce_in_context_no_middleware(self):
        response = self.client.get("/csp_nonce/")
        self.assertIn("csp_nonce", response.context)