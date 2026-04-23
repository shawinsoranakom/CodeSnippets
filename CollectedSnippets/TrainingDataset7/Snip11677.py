def as_sql(self, compiler, connection):
        sql, params = compiler.compile(self.lhs)
        tzname = None
        if isinstance(self.lhs.output_field, DateTimeField):
            tzname = self.get_tzname()
        elif self.tzinfo is not None:
            raise ValueError("tzinfo can only be used with DateTimeField.")
        if isinstance(self.output_field, DateTimeField):
            sql, params = connection.ops.datetime_trunc_sql(
                self.kind, sql, tuple(params), tzname
            )
        elif isinstance(self.output_field, DateField):
            sql, params = connection.ops.date_trunc_sql(
                self.kind, sql, tuple(params), tzname
            )
        elif isinstance(self.output_field, TimeField):
            sql, params = connection.ops.time_trunc_sql(
                self.kind, sql, tuple(params), tzname
            )
        else:
            raise ValueError(
                "Trunc only valid on DateField, TimeField, or DateTimeField."
            )
        return sql, params