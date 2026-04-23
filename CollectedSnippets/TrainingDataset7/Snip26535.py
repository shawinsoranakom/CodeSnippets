def test_csp_disabled_enforced(self):
        """
        `csp_override({})` only disables the enforced CSP header.
        """
        response = self.client.get("/csp-disabled-enforced/")
        self.assertNotIn(CSP.HEADER_ENFORCE, response)
        self.assertEqual(response[CSP.HEADER_REPORT_ONLY], basic_policy)