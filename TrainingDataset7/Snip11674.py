def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="STRFTIME('%%%%Y-%%%%m-%%%%d %%%%H:%%%%M:%%%%f', 'NOW')",
            **extra_context,
        )