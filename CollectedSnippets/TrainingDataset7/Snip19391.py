def test_no_sts_preload(self):
        """
        Warn if SECURE_HSTS_PRELOAD isn't True.
        """
        self.assertEqual(base.check_sts_preload(None), [base.W021])