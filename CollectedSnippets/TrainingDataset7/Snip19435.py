def test_with_invalid_coop(self):
        self.assertEqual(base.check_cross_origin_opener_policy(None), [base.E024])