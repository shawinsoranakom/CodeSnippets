def test_config_with_nonce(self):
        policy = {"default-src": [CSP.SELF, CSP.NONCE]}
        self.assertPolicyEqual(
            build_policy(policy, nonce="abc123"),
            "default-src 'self' 'nonce-abc123'",
        )