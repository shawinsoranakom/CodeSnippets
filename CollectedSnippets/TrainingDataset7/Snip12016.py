def using(self, alias):
        """Select which database this QuerySet should execute against."""
        clone = self._chain()
        clone._db = alias
        return clone