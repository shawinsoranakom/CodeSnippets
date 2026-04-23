def test_csp_basic(self):
        """
        With SECURE_CSP set to a valid value, the middleware adds a
        "Content-Security-Policy" header to the response.
        """
        response = self.client.get("/csp-base/")
        self.assertEqual(response[CSP.HEADER_ENFORCE], basic_policy)
        self.assertNotIn(CSP.HEADER_REPORT_ONLY, response)