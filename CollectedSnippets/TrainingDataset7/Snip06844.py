def get_prep_value(self, value):
        if not isinstance(value, Area):
            raise ValueError("AreaField only accepts Area measurement objects.")
        return value