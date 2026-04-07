def test_config_value_boolean_true(self):
        policy = {"default-src": [CSP.SELF], "block-all-mixed-content": True}
        self.assertPolicyEqual(
            build_policy(policy), "default-src 'self'; block-all-mixed-content"
        )