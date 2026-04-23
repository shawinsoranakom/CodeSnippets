def check_rhs_length_equals_lhs_length(self):
        len_lhs = len(self.lhs)
        if len_lhs != len(self.rhs):
            lhs_str = self.get_lhs_str()
            raise ValueError(
                f"{self.lookup_name!r} lookup of {lhs_str} must have {len_lhs} elements"
            )