def test_csp_nonce_in_header(self):
        response = self.client.get("/csp_nonce/")
        self.assertIn(CSP.HEADER_ENFORCE, response.headers)
        csp_header = response.headers[CSP.HEADER_ENFORCE]
        nonce = response.context["csp_nonce"]
        self.assertIn(f"'nonce-{nonce}'", csp_header)