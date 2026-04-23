def test_no_decorators(self):
        response = self.client.get("/csp-base/")
        self.assertEqual(response[CSP.HEADER_ENFORCE], basic_policy)
        self.assertEqual(response[CSP.HEADER_REPORT_ONLY], basic_policy)