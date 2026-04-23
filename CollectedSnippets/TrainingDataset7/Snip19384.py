def test_no_sts(self):
        """
        Warn if SECURE_HSTS_SECONDS isn't > 0.
        """
        self.assertEqual(base.check_sts(None), [base.W004])