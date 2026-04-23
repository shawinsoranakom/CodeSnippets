def as_sql(self, compiler, connection, **extra_context):
        if (
            self.distinct
            and not connection.features.supports_aggregate_distinct_multiple_argument
            and len(super().get_source_expressions()) > 1
        ):
            raise NotSupportedError(
                f"{self.name} does not support distinct with multiple expressions on "
                f"this database backend."
            )

        distinct_sql = "DISTINCT " if self.distinct else ""
        order_by_sql = ""
        order_by_params = []
        filter_sql = ""
        filter_params = []

        if (order_by := self.order_by) is not None:
            order_by_sql, order_by_params = compiler.compile(order_by)

        if self.filter is not None:
            try:
                filter_sql, filter_params = compiler.compile(self.filter)
            except NotSupportedError:
                # Fallback to a CASE statement on backends that don't support
                # the FILTER clause.
                copy = self.copy()
                copy.filter = None
                source_expressions = copy.get_source_expressions()
                condition = When(self.filter.condition, then=source_expressions[0])
                copy.set_source_expressions([Case(condition)] + source_expressions[1:])
                return copy.as_sql(compiler, connection, **extra_context)

        extra_context.update(
            distinct=distinct_sql,
            filter=filter_sql,
            order_by=order_by_sql,
        )
        sql, params = super().as_sql(compiler, connection, **extra_context)
        return sql, (*params, *order_by_params, *filter_params)