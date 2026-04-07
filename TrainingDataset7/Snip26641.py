def test_same_origin(self):
        """
        The X_FRAME_OPTIONS setting can be set to SAMEORIGIN to have the
        middleware use that value for the HTTP header.
        """
        with override_settings(X_FRAME_OPTIONS="SAMEORIGIN"):
            r = XFrameOptionsMiddleware(get_response_empty)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "SAMEORIGIN")

        with override_settings(X_FRAME_OPTIONS="sameorigin"):
            r = XFrameOptionsMiddleware(get_response_empty)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "SAMEORIGIN")