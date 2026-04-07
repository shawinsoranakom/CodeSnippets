def as_sqlite(self, compiler, connection, **extra_context):
        """Use the MIN function on SQLite."""
        return super().as_sqlite(compiler, connection, function="MIN", **extra_context)