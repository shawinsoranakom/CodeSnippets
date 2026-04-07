def as_sql(self, compiler, connection, **extra_context):
        if not connection.features.supports_aggregate_order_by_clause:
            raise NotSupportedError(
                "This database backend does not support specifying an order on "
                "aggregates."
            )

        return super().as_sql(compiler, connection, **extra_context)