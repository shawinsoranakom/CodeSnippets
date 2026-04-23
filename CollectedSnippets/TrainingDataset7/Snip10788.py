def contains_subquery(self):
        return any(
            expr and (getattr(expr, "subquery", False) or expr.contains_subquery)
            for expr in self.get_source_expressions()
        )