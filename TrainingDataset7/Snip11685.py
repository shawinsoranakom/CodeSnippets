def as_postgresql(self, compiler, connection, **extra_context):
        # Casting source expressions is only required using JSONB_BUILD_ARRAY
        # or when using JSON_ARRAY on PostgreSQL 16+ with server-side bindings.
        # This is done in all cases for consistency.
        casted_obj = self.copy()
        casted_obj.set_source_expressions(
            [
                (
                    # Conditional Cast to avoid unnecessary wrapping.
                    expression
                    if isinstance(expression, Cast)
                    else Cast(expression, expression.output_field)
                )
                for expression in casted_obj.get_source_expressions()
            ]
        )

        if connection.features.is_postgresql_16:
            return casted_obj.as_native(
                compiler, connection, returning="JSONB", **extra_context
            )

        return casted_obj.as_sql(
            compiler,
            connection,
            function="JSONB_BUILD_ARRAY",
            **extra_context,
        )