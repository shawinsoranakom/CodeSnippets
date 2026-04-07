def get_prep_value(self, value):
        return value.value if isinstance(value, enum.Enum) else value