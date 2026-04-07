def test_allowed_hosts_set(self):
        self.assertEqual(base.check_allowed_hosts(None), [])