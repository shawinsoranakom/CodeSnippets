def as_mysql(self, compiler, connection):
        return self.as_sql(
            compiler, connection, template="JSON_CONTAINS_PATH(%s, 'one', %s)"
        )