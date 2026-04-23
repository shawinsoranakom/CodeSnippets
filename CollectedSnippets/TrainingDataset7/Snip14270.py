def lists(self):
        """Yield (key, list) pairs."""
        return iter(super().items())