def _check_test_client_response(self, response, attribute, method_name):
        """
        Raise a ValueError if the given response doesn't have the required
        attribute.
        """
        if not hasattr(response, attribute):
            raise ValueError(
                f"{method_name}() is only usable on responses fetched using "
                "the Django test Client."
            )