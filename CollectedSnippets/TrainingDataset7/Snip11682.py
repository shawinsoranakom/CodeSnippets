def as_sql(self, compiler, connection):
        # Cast to time rather than truncate to time.
        sql, params = compiler.compile(self.lhs)
        tzname = self.get_tzname()
        return connection.ops.datetime_cast_time_sql(sql, tuple(params), tzname)