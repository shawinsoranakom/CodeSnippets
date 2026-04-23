def as_oracle(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler, connection, template="(1 / TAN(%(expressions)s))", **extra_context
        )