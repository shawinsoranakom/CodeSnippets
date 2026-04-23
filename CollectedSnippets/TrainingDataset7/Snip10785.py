def contains_aggregate(self):
        return any(
            expr and expr.contains_aggregate for expr in self.get_source_expressions()
        )