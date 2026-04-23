def none(self):
        """Return an empty QuerySet."""
        clone = self._chain()
        clone.query.set_empty()
        return clone