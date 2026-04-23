def test_allowed_hosts_empty(self):
        self.assertEqual(base.check_allowed_hosts(None), [base.W020])