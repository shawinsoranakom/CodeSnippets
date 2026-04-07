def lookups(self, request, model_admin):
        """
        Must be overridden to return a list of tuples (value, verbose value)
        """
        raise NotImplementedError(
            "The SimpleListFilter.lookups() method must be overridden to "
            "return a list of tuples (value, verbose value)."
        )