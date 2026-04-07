def as_sqlite(self, compiler, connection, **extra_context):
        # Casting to numeric is unnecessary.
        return self.as_sql(compiler, connection, **extra_context)