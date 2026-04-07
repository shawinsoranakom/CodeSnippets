def test_x_frame_options_not_deny(self):
        """
        Warn if XFrameOptionsMiddleware is in MIDDLEWARE but
        X_FRAME_OPTIONS isn't 'DENY'.
        """
        self.assertEqual(base.check_xframe_deny(None), [base.W019])