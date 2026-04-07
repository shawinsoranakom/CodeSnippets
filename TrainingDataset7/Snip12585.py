def __iter__(self):
        """Yield the forms in the order they should be rendered."""
        return iter(self.forms)