def to_python(self, value):
        if isinstance(value, str):
            value = json.loads(value)
        return value