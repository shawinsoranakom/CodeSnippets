def check_rhs_is_query(self):
        if not isinstance(self.rhs, (Query, Subquery)):
            lhs_str = self.get_lhs_str()
            rhs_cls = self.rhs.__class__.__name__
            raise ValueError(
                f"{self.lookup_name!r} subquery lookup of {lhs_str} "
                f"must be a Query object (received {rhs_cls!r})"
            )