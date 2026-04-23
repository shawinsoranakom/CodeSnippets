def contains_column_references(self):
        return any(
            expr and expr.contains_column_references
            for expr in self.get_source_expressions()
        )