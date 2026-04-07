def as_sql(self, compiler, *args, **kwargs):
        try:
            return super().as_sql(compiler, *args, **kwargs)
        except EmptyResultSet:
            features = compiler.connection.features
            if not features.supports_boolean_expr_in_select_clause:
                return "1=0", ()
            return compiler.compile(Value(False))