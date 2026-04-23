def check_rhs_elements_length_equals_lhs_length(self):
        len_lhs = len(self.lhs)
        if not all(len_lhs == len(vals) for vals in self.rhs):
            lhs_str = self.get_lhs_str()
            raise ValueError(
                f"{self.lookup_name!r} lookup of {lhs_str} "
                f"must have {len_lhs} elements each"
            )