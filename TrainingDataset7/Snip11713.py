def as_postgresql(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler,
            connection,
            template="ENCODE(DIGEST(%(expressions)s, '%(function)s'), 'hex')",
            function=self.function.lower(),
            **extra_context,
        )