def get_prep_lhs(self):
        if hasattr(self.lhs, "resolve_expression"):
            return self.lhs
        return Value(self.lhs)