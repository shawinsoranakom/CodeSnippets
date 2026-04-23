def as_sqlite(self, compiler, connection, **extra_context):
        sql, params = super().as_sql(compiler, connection, **extra_context)
        return "NULLIF(%s, -1)" % sql, params