def get_prep_lookup(self):
        if not isinstance(self.rhs, (list, tuple, Range)):
            return Cast(self.rhs, self.lhs.field.base_field)
        return super().get_prep_lookup()