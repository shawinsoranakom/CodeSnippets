def as_sqlite(self, compiler, connection, **extra_context):
        return self.get_substr().as_sqlite(compiler, connection, **extra_context)