def prepare_value(self, value):
        if isinstance(value, list):
            return self.delimiter.join(
                str(self.base_field.prepare_value(v)) for v in value
            )
        return value