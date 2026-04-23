def as_postgresql(self, compiler, connection, **extra_context):
        if connection.features.supports_uuid7_function:
            return self.as_sql(compiler, connection, **extra_context)
        raise NotSupportedError("UUID7 requires PostgreSQL version 18 or later.")