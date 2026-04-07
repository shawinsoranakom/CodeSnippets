def test_non_sensitive_request(self):
        """
        Everything (request info and frame variables) can bee seen
        in the default error reports for non-sensitive requests.
        """
        with self.settings(DEBUG=True):
            self.verify_unsafe_response(non_sensitive_view)
            self.verify_unsafe_email(non_sensitive_view)

        with self.settings(DEBUG=False):
            self.verify_unsafe_response(non_sensitive_view)
            self.verify_unsafe_email(non_sensitive_view)