def test_csp_404_debug_view(self):
        """
        Test that the CSP headers are not added to the debug view.
        """
        response = self.client.get("/csp-404/")
        self.assertNotIn(CSP.HEADER_ENFORCE, response)
        self.assertNotIn(CSP.HEADER_REPORT_ONLY, response)