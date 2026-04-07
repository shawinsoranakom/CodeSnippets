def as_sql(self, compiler, connection):
        # Cast to date rather than truncate to date.
        sql, params = compiler.compile(self.lhs)
        tzname = self.get_tzname()
        return connection.ops.datetime_cast_date_sql(sql, tuple(params), tzname)