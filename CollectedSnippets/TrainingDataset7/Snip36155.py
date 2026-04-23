def test_config_with_multiple_nonces(self):
        policy = {
            "default-src": [CSP.SELF, CSP.NONCE],
            "script-src": [CSP.SELF, CSP.NONCE],
        }
        self.assertPolicyEqual(
            build_policy(policy, nonce="abc123"),
            "default-src 'self' 'nonce-abc123'; script-src 'self' 'nonce-abc123'",
        )