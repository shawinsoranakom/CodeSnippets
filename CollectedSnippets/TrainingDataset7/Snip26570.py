def test_coop_on(self):
        """
        With SECURE_CROSS_ORIGIN_OPENER_POLICY set to a valid value, the
        middleware adds a "Cross-Origin_Opener-Policy" header to the response.
        """
        tests = ["same-origin", "same-origin-allow-popups", "unsafe-none"]
        for value in tests:
            with (
                self.subTest(value=value),
                override_settings(
                    SECURE_CROSS_ORIGIN_OPENER_POLICY=value,
                ),
            ):
                self.assertEqual(
                    self.process_response().headers["Cross-Origin-Opener-Policy"],
                    value,
                )