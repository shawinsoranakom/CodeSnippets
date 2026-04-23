def distance_expr_for_lookup(self, lhs, rhs, **kwargs):
        return super().distance_expr_for_lookup(
            self._normalize_distance_lookup_arg(lhs),
            self._normalize_distance_lookup_arg(rhs),
            **kwargs,
        )