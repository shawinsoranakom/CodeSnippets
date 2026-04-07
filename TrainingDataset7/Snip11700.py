def as_mysql(self, compiler, connection, **extra_context):
        return super().as_sql(compiler, connection, function="RAND", **extra_context)