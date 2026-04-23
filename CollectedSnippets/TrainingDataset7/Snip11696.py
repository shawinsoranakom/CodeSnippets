def as_oracle(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler,
            connection,
            template="((%%(expressions)s) * 180 / %s)" % math.pi,
            **extra_context,
        )