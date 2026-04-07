def _enable_cloning(self):
        """
        Allow calls to _chain() to create a new QuerySet via _clone(). Restores
        the default behavior where any QuerySet mutation will return a new
        QuerySet instance. Necessary only when there has been a
        _disable_cloning() call previously.
        """
        self._cloning_enabled = True
        return self