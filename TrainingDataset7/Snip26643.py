def test_defaults_sameorigin(self):
        """
        If the X_FRAME_OPTIONS setting is not set then it defaults to
        DENY.
        """
        with override_settings(X_FRAME_OPTIONS=None):
            del settings.X_FRAME_OPTIONS  # restored by override_settings
            r = XFrameOptionsMiddleware(get_response_empty)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "DENY")