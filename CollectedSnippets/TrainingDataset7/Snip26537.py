def test_csp_disabled_both(self):
        """
        Using both CSP decorators with empty mappings will clear both headers.
        """
        response = self.client.get("/csp-disabled-both/")
        self.assertNotIn(CSP.HEADER_ENFORCE, response)
        self.assertNotIn(CSP.HEADER_REPORT_ONLY, response)