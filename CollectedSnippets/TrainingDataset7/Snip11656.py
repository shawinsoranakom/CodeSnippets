def as_postgresql(self, compiler, connection, **extra_context):
        # CAST would be valid too, but the :: shortcut syntax is more readable.
        # 'expressions' is wrapped in parentheses in case it's a complex
        # expression.
        return self.as_sql(
            compiler,
            connection,
            template="(%(expressions)s)::%(db_type)s",
            **extra_context,
        )