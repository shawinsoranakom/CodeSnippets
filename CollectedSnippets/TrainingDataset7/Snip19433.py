def test_no_coop(self):
        self.assertEqual(base.check_cross_origin_opener_policy(None), [])