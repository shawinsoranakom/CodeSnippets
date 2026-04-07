def get_prep_value(self, value):
        if isinstance(value, Distance):
            return value
        return super().get_prep_value(value)