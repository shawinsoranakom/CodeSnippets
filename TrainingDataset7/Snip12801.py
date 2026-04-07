def options(self, name, value, attrs=None):
        """Yield a flat list of options for this widget."""
        for group in self.optgroups(name, value, attrs):
            yield from group[1]