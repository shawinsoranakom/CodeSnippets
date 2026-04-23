def test_sts_preload(self):
        """
        With SECURE_HSTS_SECONDS non-zero and SECURE_HSTS_PRELOAD True, the
        middleware adds a "Strict-Transport-Security" header with the "preload"
        directive to the response.
        """
        response = self.process_response(secure=True)
        self.assertEqual(
            response.headers["Strict-Transport-Security"],
            "max-age=10886400; preload",
        )