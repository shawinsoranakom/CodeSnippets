def test_csp_report_only_basic(self):
        """
        With SECURE_CSP_REPORT_ONLY set to a valid value, the middleware adds a
        "Content-Security-Policy-Report-Only" header to the response.
        """
        response = self.client.get("/csp-base/")
        self.assertEqual(response[CSP.HEADER_REPORT_ONLY], basic_policy)
        self.assertNotIn(CSP.HEADER_ENFORCE, response)