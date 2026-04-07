def get_source_expressions(self):
        if self.rhs_is_direct_value():
            return [self.lhs]
        return [self.lhs, self.rhs]