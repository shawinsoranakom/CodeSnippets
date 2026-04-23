def test_coop_default(self):
        """SECURE_CROSS_ORIGIN_OPENER_POLICY defaults to same-origin."""
        self.assertEqual(
            self.process_response().headers["Cross-Origin-Opener-Policy"],
            "same-origin",
        )