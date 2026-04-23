def check_rhs_is_supported_expression(self):
        if not isinstance(self.rhs, (ResolvedOuterRef, Query)):
            lhs_str = self.get_lhs_str()
            rhs_cls = self.rhs.__class__.__name__
            raise ValueError(
                f"{self.lookup_name!r} subquery lookup of {lhs_str} "
                f"only supports OuterRef and QuerySet objects (received {rhs_cls!r})"
            )