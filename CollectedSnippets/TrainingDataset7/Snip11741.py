def as_sql(self, compiler, connection, **extra_context):
        if connection.features.supports_uuid4_function:
            return super().as_sql(compiler, connection, **extra_context)
        raise NotSupportedError("UUID4 is not supported on this database backend.")