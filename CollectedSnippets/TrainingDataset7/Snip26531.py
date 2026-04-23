def test_csp_both(self):
        """
        If both SECURE_CSP and SECURE_CSP_REPORT_ONLY are set, the middleware
        adds both headers to the response.
        """
        response = self.client.get("/csp-base/")
        self.assertEqual(response[CSP.HEADER_ENFORCE], basic_policy)
        self.assertEqual(response[CSP.HEADER_REPORT_ONLY], basic_policy)