def filter(self, *args, **kwargs):
        """
        Return a new QuerySet instance with the args ANDed to the existing
        set.
        """
        self._not_support_combined_queries("filter")
        return self._filter_or_exclude(False, args, kwargs)