def as_sql(self, compiler, connection, **extra_context):
        extra_context.setdefault("collation", connection.ops.quote_name(self.collation))
        return super().as_sql(compiler, connection, **extra_context)