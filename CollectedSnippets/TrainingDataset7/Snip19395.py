def test_middleware_not_installed(self):
        """
        Warn if XFrameOptionsMiddleware isn't in MIDDLEWARE.
        """
        self.assertEqual(base.check_xframe_options_middleware(None), [base.W002])