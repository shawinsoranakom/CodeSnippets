def _disable_cloning(self):
        """
        Prevent calls to _chain() from creating a new QuerySet via _clone().
        All subsequent QuerySet mutations will occur on this instance until
        _enable_cloning() is used.
        """
        self._cloning_enabled = False
        return self