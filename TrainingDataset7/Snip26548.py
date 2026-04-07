def test_sts_on(self):
        """
        With SECURE_HSTS_SECONDS=3600, the middleware adds
        "Strict-Transport-Security: max-age=3600" to the response.
        """
        self.assertEqual(
            self.process_response(secure=True).headers["Strict-Transport-Security"],
            "max-age=3600",
        )