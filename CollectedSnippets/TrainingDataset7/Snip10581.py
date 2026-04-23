def resolve_expression(self, *args, **kwargs):
        result = super().resolve_expression(*args, **kwargs)
        source_expressions = result.get_source_expressions()

        # In case of composite primary keys, count the first column.
        if isinstance(expr := source_expressions[0], ColPairs):
            if self.distinct:
                raise ValueError(
                    "COUNT(DISTINCT) doesn't support composite primary keys"
                )

            source_expressions[0] = expr.get_cols()[0]
            result.set_source_expressions(source_expressions)

        return result