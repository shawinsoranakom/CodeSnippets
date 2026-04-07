def as_oracle(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler,
            connection,
            template="%(function)s(%(expressions)s USING NCHAR_CS)",
            **extra_context,
        )