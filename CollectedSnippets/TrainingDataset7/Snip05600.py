def expected_parameters(self):
        """
        Return the list of parameter names that are expected from the
        request's query string and that will be used by this filter.
        """
        raise NotImplementedError(
            "subclasses of ListFilter must provide an expected_parameters() method"
        )