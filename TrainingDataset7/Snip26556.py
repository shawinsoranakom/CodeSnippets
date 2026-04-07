def test_sts_no_preload(self):
        """
        With SECURE_HSTS_SECONDS non-zero and SECURE_HSTS_PRELOAD
        False, the middleware adds a "Strict-Transport-Security" header without
        the "preload" directive to the response.
        """
        response = self.process_response(secure=True)
        self.assertEqual(
            response.headers["Strict-Transport-Security"],
            "max-age=10886400",
        )