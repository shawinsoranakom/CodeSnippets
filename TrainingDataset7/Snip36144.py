def test_config_basic(self):
        self.assertPolicyEqual(build_policy(basic_config), basic_policy)