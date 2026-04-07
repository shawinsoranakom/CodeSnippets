def test_with_sts_preload(self):
        self.assertEqual(base.check_sts_preload(None), [])