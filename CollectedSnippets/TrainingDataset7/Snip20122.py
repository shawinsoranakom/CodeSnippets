def as_sql(self, compiler, connection):
        lhs_sql, params = compiler.compile(self.lhs)
        return connection.ops.date_extract_sql("year", lhs_sql, params)