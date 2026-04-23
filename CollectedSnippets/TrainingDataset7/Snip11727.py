def as_mysql(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler, connection, function="CHAR_LENGTH", **extra_context
        )