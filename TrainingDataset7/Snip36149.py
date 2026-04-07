def test_config_value_none(self):
        """
        Test that `None` removes the directive from the policy.

        Useful in cases where the CSP config is scripted in some way or
        explicitly not wanting to set a directive.
        """
        policy = {"default-src": [CSP.SELF], "script-src": None}
        self.assertPolicyEqual(build_policy(policy), basic_policy)