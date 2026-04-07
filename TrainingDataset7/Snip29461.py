def to_python(self, value):
        if isinstance(value, Tag):
            return value
        if value is None:
            return value
        return Tag(int(value))