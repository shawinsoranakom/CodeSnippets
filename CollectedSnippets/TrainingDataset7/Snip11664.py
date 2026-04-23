def as_sqlite(self, compiler, connection, **extra_context):
        """Use the MAX function on SQLite."""
        return super().as_sqlite(compiler, connection, function="MAX", **extra_context)