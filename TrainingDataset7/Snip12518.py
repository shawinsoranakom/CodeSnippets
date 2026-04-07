def to_python(self, value):
        """Return a string."""
        if value in self.empty_values:
            return ""
        return str(value)