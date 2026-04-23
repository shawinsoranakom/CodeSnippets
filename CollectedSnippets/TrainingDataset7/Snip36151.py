def test_config_value_boolean_false(self):
        policy = {"default-src": [CSP.SELF], "block-all-mixed-content": False}
        self.assertPolicyEqual(build_policy(policy), basic_policy)