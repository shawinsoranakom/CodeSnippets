def test_config_value_as_string(self):
        """
        Test that a single value can be passed as a string.
        """
        policy = {"default-src": CSP.SELF}
        self.assertPolicyEqual(build_policy(policy), "default-src 'self'")