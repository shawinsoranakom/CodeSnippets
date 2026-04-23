def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return None
        return self.to_python(value)