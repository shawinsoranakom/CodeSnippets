def as_mysql(self, compiler, connection, **extra_context):
        # Use CONCAT_WS with an empty separator so that NULLs are ignored.
        return super().as_sql(
            compiler,
            connection,
            function="CONCAT_WS",
            template="%(function)s('', %(expressions)s)",
            **extra_context,
        )