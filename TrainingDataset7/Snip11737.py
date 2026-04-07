def as_postgresql(self, compiler, connection, **extra_context):
        return super().as_sql(compiler, connection, function="STRPOS", **extra_context)