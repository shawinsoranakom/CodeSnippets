def test_no_referrer_policy(self):
        self.assertEqual(base.check_referrer_policy(None), [base.W022])