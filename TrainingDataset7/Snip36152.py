def test_config_value_multiple_boolean(self):
        policy = {
            "default-src": [CSP.SELF],
            "block-all-mixed-content": True,
            "upgrade-insecure-requests": True,
        }
        self.assertPolicyEqual(
            build_policy(policy),
            "default-src 'self'; block-all-mixed-content; upgrade-insecure-requests",
        )