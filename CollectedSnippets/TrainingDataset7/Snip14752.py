def __contains__(self, other):
        """Return True if 'other' is a direct child of this instance."""
        return other in self.children