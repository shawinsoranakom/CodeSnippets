def as_postgresql(self, compiler, connection, **extra_context):
        if connection.features.is_postgresql_18:
            return self.as_sql(compiler, connection, **extra_context)
        return self.as_sql(
            compiler, connection, function="GEN_RANDOM_UUID", **extra_context
        )