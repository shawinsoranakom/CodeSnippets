def check_rhs_is_tuple_or_list(self):
        if not isinstance(self.rhs, (tuple, list)):
            lhs_str = self.get_lhs_str()
            raise ValueError(
                f"{self.lookup_name!r} lookup of {lhs_str} must be a tuple or a list"
            )