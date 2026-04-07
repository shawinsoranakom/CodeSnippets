def test_config_with_empty_directive(self):
        policy = {"default-src": []}
        self.assertPolicyEqual(build_policy(policy), "")