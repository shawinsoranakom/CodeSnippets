def test_with_sts_subdomains(self):
        self.assertEqual(base.check_sts_include_subdomains(None), [])