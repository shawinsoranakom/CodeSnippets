def get_prep_lookup(self):
        return RangeField().get_prep_value(self.rhs)