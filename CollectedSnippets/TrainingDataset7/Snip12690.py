def to_python(self, value):
        if not value:
            return []
        return list(self._check_values(value))