def test_coop_off(self):
        """
        With SECURE_CROSS_ORIGIN_OPENER_POLICY set to None, the middleware does
        not add a "Cross-Origin-Opener-Policy" header to the response.
        """
        self.assertNotIn("Cross-Origin-Opener-Policy", self.process_response())