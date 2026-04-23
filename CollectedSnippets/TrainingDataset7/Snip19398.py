def test_middleware_not_installed(self):
        """
        No error if XFrameOptionsMiddleware isn't in MIDDLEWARE even if
        X_FRAME_OPTIONS isn't 'DENY'.
        """
        self.assertEqual(base.check_xframe_deny(None), [])