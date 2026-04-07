def test_async_sensitive_request_nested(self):
        """
        Sensitive POST parameters cannot be seen in the default
        error reports for sensitive requests.
        """
        with self.settings(DEBUG=True):
            self.verify_unsafe_response(
                async_sensitive_view_nested, check_for_vars=False
            )

        with self.settings(DEBUG=False):
            self.verify_safe_response(async_sensitive_view_nested, check_for_vars=False)