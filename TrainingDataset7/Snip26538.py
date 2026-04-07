def test_csp_override_enforced(self):
        """
        `csp_override` only overrides the enforced header.
        """
        response = self.client.get("/csp-override-enforced/")
        self.assertEqual(
            response[CSP.HEADER_ENFORCE], "default-src 'self'; img-src 'self' data:"
        )
        self.assertEqual(response[CSP.HEADER_REPORT_ONLY], basic_policy)