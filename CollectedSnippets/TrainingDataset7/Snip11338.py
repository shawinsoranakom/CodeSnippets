def as_sqlite(self, compiler, connection):
        return self.as_sql(
            compiler, connection, template="JSON_TYPE(%s, %s) IS NOT NULL"
        )