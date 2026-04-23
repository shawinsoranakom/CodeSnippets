def test_no_referrer_policy_no_middleware(self):
        """
        Don't warn if SECURE_REFERRER_POLICY is None and SecurityMiddleware
        isn't in MIDDLEWARE.
        """
        self.assertEqual(base.check_referrer_policy(None), [])