def test_sts_include_subdomains(self):
        """
        With SECURE_HSTS_SECONDS non-zero and SECURE_HSTS_INCLUDE_SUBDOMAINS
        True, the middleware adds a "Strict-Transport-Security" header with the
        "includeSubDomains" directive to the response.
        """
        response = self.process_response(secure=True)
        self.assertEqual(
            response.headers["Strict-Transport-Security"],
            "max-age=600; includeSubDomains",
        )