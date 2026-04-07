def test_no_sts_subdomains(self):
        """
        Warn if SECURE_HSTS_INCLUDE_SUBDOMAINS isn't True.
        """
        self.assertEqual(base.check_sts_include_subdomains(None), [base.W005])