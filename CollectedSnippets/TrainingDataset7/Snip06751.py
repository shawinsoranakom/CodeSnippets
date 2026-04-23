def as_oracle(self, compiler, connection, **extra_context):
        if not self.is_extent:
            tolerance = self.extra.get("tolerance") or getattr(self, "tolerance", 0.05)
            clone = self.copy()
            *source_exprs, filter_expr, order_by_expr = self.get_source_expressions()
            spatial_type_expr = Func(
                *source_exprs,
                Value(tolerance),
                function="SDOAGGRTYPE",
                output_field=self.output_field,
            )
            source_expressions = [spatial_type_expr, filter_expr, order_by_expr]
            clone.set_source_expressions(source_expressions)
            return clone.as_sql(compiler, connection, **extra_context)
        return self.as_sql(compiler, connection, **extra_context)