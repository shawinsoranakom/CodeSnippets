def test_sts_subdomains_and_preload(self):
        """
        With SECURE_HSTS_SECONDS non-zero, SECURE_HSTS_INCLUDE_SUBDOMAINS and
        SECURE_HSTS_PRELOAD True, the middleware adds a
        "Strict-Transport-Security" header containing both the
        "includeSubDomains" and "preload" directives to the response.
        """
        response = self.process_response(secure=True)
        self.assertEqual(
            response.headers["Strict-Transport-Security"],
            "max-age=10886400; includeSubDomains; preload",
        )