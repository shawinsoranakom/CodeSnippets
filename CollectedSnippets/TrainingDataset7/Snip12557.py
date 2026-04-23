def __iter__(self):
        """Yield the form's fields as BoundField objects."""
        for name in self.fields:
            yield self[name]