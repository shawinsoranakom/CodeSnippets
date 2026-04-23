def as_mysql(self, compiler, connection):
        sql, params = self.as_sql(compiler, connection)
        sql = "JSON_EXTRACT(%s, '$')"
        return sql, params