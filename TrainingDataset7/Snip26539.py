def test_csp_report_only_override(self):
        """
        `csp_report_only_override` only overrides the report-only header.
        """
        response = self.client.get("/csp-override-report-only/")
        self.assertEqual(
            response[CSP.HEADER_REPORT_ONLY], "default-src 'self'; img-src 'self' data:"
        )
        self.assertEqual(response[CSP.HEADER_ENFORCE], basic_policy)