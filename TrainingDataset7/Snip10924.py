def as_sql(self, compiler, connection):
        try:
            sql, params = super().as_sql(compiler, connection)
        except EmptyResultSet:
            features = compiler.connection.features
            if not features.supports_boolean_expr_in_select_clause:
                return "1=1", ()
            return compiler.compile(Value(True))
        ops = compiler.connection.ops
        # Some database backends (e.g. Oracle) don't allow EXISTS() and filters
        # to be compared to another expression unless they're wrapped in a CASE
        # WHEN.
        if not ops.conditional_expression_supported_in_where_clause(self.expression):
            return f"CASE WHEN {sql} = 0 THEN 1 ELSE 0 END", params
        return f"NOT {sql}", params