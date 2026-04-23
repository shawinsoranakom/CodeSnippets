def prepare_value(self, value):
        if isinstance(value, uuid.UUID):
            return str(value)
        return value