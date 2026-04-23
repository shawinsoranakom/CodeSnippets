def test_no_security_middleware(self):
        """
        Warn if SecurityMiddleware isn't in MIDDLEWARE.
        """
        self.assertEqual(base.check_security_middleware(None), [base.W001])