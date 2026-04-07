def as_mysql(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler,
            connection,
            template="SHA2(%%(expressions)s, %s)" % self.function[3:],
            **extra_context,
        )