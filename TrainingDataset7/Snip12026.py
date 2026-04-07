def _chain(self):
        """
        Return a copy of the current QuerySet that's ready for another
        operation.

        If the QuerySet has opted in to in-place mutations via
        _disable_cloning() temporarily, the copy doesn't occur and instead the
        same QuerySet instance will be modified.
        """
        if not self._cloning_enabled:
            obj = self
        else:
            obj = self._clone()
        if obj._sticky_filter:
            obj.query.filter_is_sticky = True
            obj._sticky_filter = False
        return obj