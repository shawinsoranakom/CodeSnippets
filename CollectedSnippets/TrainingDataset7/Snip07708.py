def to_python(self, value):
        if isinstance(value, str):
            # Assume we're deserializing
            vals = json.loads(value)
            for end in ("lower", "upper"):
                if end in vals:
                    vals[end] = self.base_field.to_python(vals[end])
            value = self.range_type(**vals)
        elif isinstance(value, (list, tuple)):
            value = self.range_type(value[0], value[1])
        return value