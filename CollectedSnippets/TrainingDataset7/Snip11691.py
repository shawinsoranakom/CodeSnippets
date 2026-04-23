def as_postgresql(self, compiler, connection, **extra_context):
        # Casting keys to text is only required when using JSONB_BUILD_OBJECT
        # or when using JSON_OBJECT on PostgreSQL 16+ with server-side
        # bindings. This is done in all cases for consistency.
        copy = self.copy()
        copy.set_source_expressions(
            [
                Cast(expression, TextField()) if index % 2 == 0 else expression
                for index, expression in enumerate(copy.get_source_expressions())
            ]
        )

        if connection.features.is_postgresql_16:
            return copy.as_native(
                compiler, connection, returning="JSONB", **extra_context
            )

        return super(JSONObject, copy).as_sql(
            compiler,
            connection,
            function="JSONB_BUILD_OBJECT",
            **extra_context,
        )