def test_config_empty(self):
        self.assertPolicyEqual(build_policy({}), "")