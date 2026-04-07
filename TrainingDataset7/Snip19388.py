def test_no_sts_subdomains_no_middleware(self):
        """
        Don't warn if SecurityMiddleware isn't installed.
        """
        self.assertEqual(base.check_sts_include_subdomains(None), [])