def test_referrer_policy_on(self):
        """
        With SECURE_REFERRER_POLICY set to a valid value, the middleware adds a
        "Referrer-Policy" header to the response.
        """
        tests = (
            ("strict-origin", "strict-origin"),
            ("strict-origin,origin", "strict-origin,origin"),
            ("strict-origin, origin", "strict-origin,origin"),
            (["strict-origin", "origin"], "strict-origin,origin"),
            (("strict-origin", "origin"), "strict-origin,origin"),
        )
        for value, expected in tests:
            with (
                self.subTest(value=value),
                override_settings(SECURE_REFERRER_POLICY=value),
            ):
                self.assertEqual(
                    self.process_response().headers["Referrer-Policy"],
                    expected,
                )