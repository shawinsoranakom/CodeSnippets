def as_sql(self, compiler, connection):
        sql, params = compiler.compile(self.lhs)
        lhs_output_field = self.lhs.output_field
        if isinstance(lhs_output_field, DateTimeField):
            tzname = self.get_tzname()
            sql, params = connection.ops.datetime_extract_sql(
                self.lookup_name, sql, tuple(params), tzname
            )
        elif self.tzinfo is not None:
            raise ValueError("tzinfo can only be used with DateTimeField.")
        elif isinstance(lhs_output_field, DateField):
            sql, params = connection.ops.date_extract_sql(
                self.lookup_name, sql, tuple(params)
            )
        elif isinstance(lhs_output_field, TimeField):
            sql, params = connection.ops.time_extract_sql(
                self.lookup_name, sql, tuple(params)
            )
        elif isinstance(lhs_output_field, DurationField):
            if not connection.features.has_native_duration_field:
                raise ValueError(
                    "Extract requires native DurationField database support."
                )
            sql, params = connection.ops.time_extract_sql(
                self.lookup_name, sql, tuple(params)
            )
        else:
            # resolve_expression has already validated the output_field so this
            # assert should never be hit.
            assert False, "Tried to Extract from an invalid type."
        return sql, params