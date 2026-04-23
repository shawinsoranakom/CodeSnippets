def test_csp_basic_with_nonce_but_unused(self):
        """
        Test if `request.csp_nonce` is never accessed, it is not added to the
        header.
        """
        response = self.client.get("/csp-base/")
        nonce = response.text
        self.assertIsNotNone(nonce)
        self.assertEqual(response[CSP.HEADER_ENFORCE], basic_policy)