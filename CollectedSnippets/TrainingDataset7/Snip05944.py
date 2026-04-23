def get_filters_params(self, params=None):
        """
        Return all params except IGNORED_PARAMS.
        """
        params = params or self.filter_params
        lookup_params = params.copy()  # a dictionary of the query string
        # Remove all the parameters that are globally and systematically
        # ignored.
        for ignored in IGNORED_PARAMS:
            if ignored in lookup_params:
                del lookup_params[ignored]
        return lookup_params