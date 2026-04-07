def prefix_references(self, prefix):
        clone = self.copy()
        clone.set_source_expressions(
            [
                (
                    F(f"{prefix}{expr.name}")
                    if isinstance(expr, F)
                    else expr.prefix_references(prefix)
                )
                for expr in self.get_source_expressions()
            ]
        )
        return clone