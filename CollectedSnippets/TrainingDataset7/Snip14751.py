def __bool__(self):
        """Return whether or not this node has children."""
        return bool(self.children)