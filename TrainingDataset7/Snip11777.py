def get_prep_lookup(self):
        if not self.prepare_rhs or hasattr(self.rhs, "resolve_expression"):
            return self.rhs
        if hasattr(self.lhs, "output_field"):
            if hasattr(self.lhs.output_field, "get_prep_value"):
                return self.lhs.output_field.get_prep_value(self.rhs)
        elif self.rhs_is_direct_value():
            return Value(self.rhs)
        return self.rhs