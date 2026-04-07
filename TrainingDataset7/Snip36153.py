def test_config_with_nonce_arg(self):
        """
        Test when the `CSP.NONCE` is not in the defined policy, the nonce
        argument has no effect.
        """
        self.assertPolicyEqual(build_policy(basic_config, nonce="abc123"), basic_policy)