def test_csp_report_only_disabled(self):
        """
        `csp_report_only_override({})` only disables the report-only header.
        """
        response = self.client.get("/csp-disabled-report-only/")
        self.assertNotIn(CSP.HEADER_REPORT_ONLY, response)
        self.assertEqual(response[CSP.HEADER_ENFORCE], basic_policy)