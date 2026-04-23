def _set_level(self, value=None):
        """
        Set a custom minimum recorded level.

        If set to ``None``, the default level will be used (see the
        ``_get_level`` method).
        """
        if value is None and hasattr(self, "_level"):
            del self._level
        else:
            self._level = int(value)