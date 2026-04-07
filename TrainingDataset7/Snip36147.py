def test_config_value_as_tuple(self):
        """
        Test that a tuple can be passed as a value.
        """
        policy = {"default-src": (CSP.SELF, "foo.com")}
        self.assertPolicyEqual(build_policy(policy), "default-src 'self' foo.com")