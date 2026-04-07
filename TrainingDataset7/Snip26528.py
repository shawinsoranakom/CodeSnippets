def test_csp_basic_with_nonce(self):
        """
        Test the nonce is added to the header and matches what is in the view.
        """
        response = self.client.get("/csp-nonce/")
        nonce = response.text
        self.assertTrue(nonce)
        self.assertEqual(
            response[CSP.HEADER_ENFORCE], f"default-src 'self' 'nonce-{nonce}'"
        )