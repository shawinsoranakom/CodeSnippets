def as_mysql(self, compiler, connection, **extra_context):
        template = " SEPARATOR %(expressions)s"

        return self.as_sql(
            compiler,
            connection,
            template=template,
            **extra_context,
        )