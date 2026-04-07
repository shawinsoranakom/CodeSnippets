def test_async_sensitive_method_nested(self):
        """
        The sensitive_variables decorator works with async object methods.
        """
        with self.settings(DEBUG=True):
            self.verify_unsafe_response(
                async_sensitive_method_view_nested, check_for_POST_params=False
            )
            self.verify_unsafe_email(
                async_sensitive_method_view_nested, check_for_POST_params=False
            )

        with self.settings(DEBUG=False):
            self.verify_safe_response(
                async_sensitive_method_view_nested, check_for_POST_params=False
            )
            self.verify_safe_email(
                async_sensitive_method_view_nested, check_for_POST_params=False
            )