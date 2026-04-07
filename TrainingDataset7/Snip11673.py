def as_mysql(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler, connection, template="CURRENT_TIMESTAMP(6)", **extra_context
        )