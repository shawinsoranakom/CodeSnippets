def as_sqlite(self, compiler, connection, **extra_context):
        copy = self.copy()
        copy.set_source_expressions(
            [
                (
                    Value(float(expr.value))
                    if hasattr(expr, "value") and isinstance(expr.value, Decimal)
                    else expr
                )
                for expr in copy.get_source_expressions()
            ]
        )
        return copy.as_sql(compiler, connection, **extra_context)