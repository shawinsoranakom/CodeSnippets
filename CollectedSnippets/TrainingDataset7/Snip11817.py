def as_sql(self, compiler, connection):
        if not isinstance(self.rhs, bool):
            raise ValueError(
                "The QuerySet value for an isnull lookup must be True or False."
            )
        if isinstance(self.lhs, Value):
            if self.lhs.value is None or (
                self.lhs.value == ""
                and connection.features.interprets_empty_strings_as_nulls
            ):
                result_exception = FullResultSet if self.rhs else EmptyResultSet
            else:
                result_exception = EmptyResultSet if self.rhs else FullResultSet
            raise result_exception
        sql, params = self.process_lhs(compiler, connection)
        if self.rhs:
            return "%s IS NULL" % sql, params
        else:
            return "%s IS NOT NULL" % sql, params