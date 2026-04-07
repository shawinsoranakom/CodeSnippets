def as_sql(self, compiler, connection, **extra_context):
        if not connection.features.supports_any_value:
            raise NotSupportedError(
                "ANY_VALUE is not supported on this database backend."
            )
        return super().as_sql(compiler, connection, **extra_context)