def test_csp_nonce_length(self):
        response = self.client.get("/csp_nonce/")
        nonce = response.context["csp_nonce"]
        self.assertEqual(len(nonce), 22)