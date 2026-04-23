def test_sts_only_if_secure(self):
        """
        The "Strict-Transport-Security" header is not added to responses going
        over an insecure connection.
        """
        self.assertNotIn(
            "Strict-Transport-Security",
            self.process_response(secure=False).headers,
        )