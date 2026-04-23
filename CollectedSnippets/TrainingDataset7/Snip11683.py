def as_sql(self, compiler, connection, **extra_context):
        if not connection.features.supports_json_field:
            raise NotSupportedError(
                "JSONFields are not supported on this database backend."
            )
        return super().as_sql(compiler, connection, **extra_context)