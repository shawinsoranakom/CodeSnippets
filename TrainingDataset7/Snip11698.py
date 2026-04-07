def as_oracle(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler, connection, template=str(math.pi), **extra_context
        )