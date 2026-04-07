def test_config_value_as_set(self):
        """
        Test that a set can be passed as a value.

        Sets are often used in Django settings to ensure uniqueness, however,
        sets are unordered. The middleware ensures consistency via sorting if a
        set is passed.
        """
        policy = {"default-src": {CSP.SELF, "foo.com", "bar.com"}}
        self.assertPolicyEqual(
            build_policy(policy), "default-src 'self' bar.com foo.com"
        )