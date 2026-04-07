def get_prep_value(self, value):
        if isinstance(value, (list, tuple)):
            return self.range_type(value[0], value[1], self.default_bounds)
        return super().get_prep_value(value)