def test_no_sts_no_middleware(self):
        """
        Don't warn if SECURE_HSTS_SECONDS isn't > 0 and SecurityMiddleware
        isn't installed.
        """
        self.assertEqual(base.check_sts(None), [])