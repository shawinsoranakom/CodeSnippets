def test_config_multiple_directives(self):
        policy = {
            "default-src": [CSP.SELF],
            "script-src": [CSP.NONE],
        }
        self.assertPolicyEqual(
            build_policy(policy), "default-src 'self'; script-src 'none'"
        )