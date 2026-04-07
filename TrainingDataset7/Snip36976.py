def test_custom_exception_reporter_filter(self):
        """
        It's possible to assign an exception reporter filter to
        the request to bypass the one set in DEFAULT_EXCEPTION_REPORTER_FILTER.
        """
        with self.settings(DEBUG=True):
            self.verify_unsafe_response(
                custom_exception_reporter_filter_view, check_for_vars=False
            )

        with self.settings(DEBUG=False):
            self.verify_unsafe_response(
                custom_exception_reporter_filter_view, check_for_vars=False
            )