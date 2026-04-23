def dict(self):
        """Return current object as a dict with singular values."""
        return {key: self[key] for key in self}