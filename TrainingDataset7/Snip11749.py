def as_sqlite(self, compiler, connection, **extra_context):
        if connection.features.supports_uuid7_function:
            return self.as_sql(compiler, connection, **extra_context)
        raise NotSupportedError(
            "UUID7 on SQLite requires Python version 3.14 or later."
        )