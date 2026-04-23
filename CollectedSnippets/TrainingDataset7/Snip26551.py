def test_sts_off(self):
        """
        With SECURE_HSTS_SECONDS=0, the middleware does not add a
        "Strict-Transport-Security" header to the response.
        """
        self.assertNotIn(
            "Strict-Transport-Security",
            self.process_response(secure=True).headers,
        )