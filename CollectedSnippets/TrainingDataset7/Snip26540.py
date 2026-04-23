def test_csp_override_both_decorator(self):
        """
        Using both CSP decorators overrides both CSP Django settings.
        """
        response = self.client.get("/csp-override-both/")
        self.assertEqual(
            response[CSP.HEADER_ENFORCE], "default-src 'self'; img-src 'self' data:"
        )
        self.assertEqual(
            response[CSP.HEADER_REPORT_ONLY], "default-src 'self'; img-src 'self' data:"
        )