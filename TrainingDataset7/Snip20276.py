def get_prep_value(self, value):
        if value is None:
            return None
        return int(value)