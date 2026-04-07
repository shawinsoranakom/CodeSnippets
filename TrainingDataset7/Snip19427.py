def test_with_invalid_referrer_policy(self):
        self.assertEqual(base.check_referrer_policy(None), [base.E023])