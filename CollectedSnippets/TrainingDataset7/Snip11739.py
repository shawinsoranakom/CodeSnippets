def as_sqlite(self, compiler, connection, **extra_context):
        return super().as_sql(compiler, connection, function="SUBSTR", **extra_context)