def test_deny(self):
        """
        The X_FRAME_OPTIONS setting can be set to DENY to have the middleware
        use that value for the HTTP header.
        """
        with override_settings(X_FRAME_OPTIONS="DENY"):
            r = XFrameOptionsMiddleware(get_response_empty)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "DENY")

        with override_settings(X_FRAME_OPTIONS="deny"):
            r = XFrameOptionsMiddleware(get_response_empty)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "DENY")