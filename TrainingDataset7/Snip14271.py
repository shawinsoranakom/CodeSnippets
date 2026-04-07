def values(self):
        """Yield the last value on every key list."""
        for key in self:
            yield self[key]