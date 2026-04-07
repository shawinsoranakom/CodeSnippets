def test_csp_defaults_off(self):
        response = self.client.get("/csp-base/")
        self.assertNotIn(CSP.HEADER_ENFORCE, response)
        self.assertNotIn(CSP.HEADER_REPORT_ONLY, response)