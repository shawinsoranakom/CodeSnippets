def as_postgresql(self, compiler, connection, **extra_context):
        # Cast FloatField to DecimalField as PostgreSQL doesn't support the
        # following function signatures:
        # - LOG(double, double)
        # - MOD(double, double)
        output_field = DecimalField(decimal_places=sys.float_info.dig, max_digits=1000)
        clone = self.copy()
        clone.set_source_expressions(
            [
                (
                    Cast(expression, output_field)
                    if isinstance(expression.output_field, FloatField)
                    else expression
                )
                for expression in self.get_source_expressions()
            ]
        )
        return clone.as_sql(compiler, connection, **extra_context)