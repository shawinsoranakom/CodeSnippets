def as_sql(self, compiler, connection, **extra_context):
        if not connection.features.supports_aggregate_filter_clause:
            raise NotSupportedError(
                "Aggregate filter clauses are not supported on this database backend."
            )
        try:
            return super().as_sql(compiler, connection, **extra_context)
        except FullResultSet:
            return "", ()