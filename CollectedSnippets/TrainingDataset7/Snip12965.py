def setdefault(self, key, value):
        """Set a header unless it has already been set."""
        self.headers.setdefault(key, value)