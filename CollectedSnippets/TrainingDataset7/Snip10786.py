def contains_over_clause(self):
        return any(
            expr and expr.contains_over_clause for expr in self.get_source_expressions()
        )