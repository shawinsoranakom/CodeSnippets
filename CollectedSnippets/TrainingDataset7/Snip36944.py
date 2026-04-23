def test_async_sensitive_request(self):
        with self.settings(DEBUG=True):
            self.verify_unsafe_response(async_sensitive_view)
            self.verify_unsafe_email(async_sensitive_view)

        with self.settings(DEBUG=False):
            self.verify_safe_response(async_sensitive_view)
            self.verify_safe_email(async_sensitive_view)