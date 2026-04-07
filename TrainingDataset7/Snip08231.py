def clear(self):
        """Remove *all* values from the cache at once."""
        raise NotImplementedError(
            "subclasses of BaseCache must provide a clear() method"
        )