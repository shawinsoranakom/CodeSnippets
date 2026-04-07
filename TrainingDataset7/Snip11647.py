def check_rhs_is_collection_of_tuples_or_lists(self):
        if not all(isinstance(vals, (tuple, list)) for vals in self.rhs):
            lhs_str = self.get_lhs_str()
            raise ValueError(
                f"{self.lookup_name!r} lookup of {lhs_str} "
                "must be a collection of tuples or lists"
            )