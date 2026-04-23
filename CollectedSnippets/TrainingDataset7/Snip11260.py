def to_python(self, value):
        if isinstance(value, str):
            # Assume we're deserializing.
            vals = json.loads(value)
            value = [
                field.to_python(val)
                for field, val in zip(self.fields, vals, strict=True)
            ]
        return value