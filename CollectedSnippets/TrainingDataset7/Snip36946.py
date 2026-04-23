def test_paranoid_request(self):
        """
        No POST parameters and frame variables can be seen in the
        default error reports for "paranoid" requests.
        """
        with self.settings(DEBUG=True):
            self.verify_unsafe_response(paranoid_view)
            self.verify_unsafe_email(paranoid_view)

        with self.settings(DEBUG=False):
            self.verify_paranoid_response(paranoid_view)
            self.verify_paranoid_email(paranoid_view)