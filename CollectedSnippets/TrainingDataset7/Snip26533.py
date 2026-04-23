def test_csp_500_debug_view(self):
        """
        Test that the CSP headers are not added to the debug view.
        """
        with self.assertLogs("django.request", "WARNING"):
            response = self.client.get("/csp-500/")
        self.assertNotIn(CSP.HEADER_ENFORCE, response)
        self.assertNotIn(CSP.HEADER_REPORT_ONLY, response)