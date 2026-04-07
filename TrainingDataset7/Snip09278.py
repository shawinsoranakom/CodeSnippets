def time_trunc_sql(self, lookup_type, sql, params, tzname=None):
        """
        Given a lookup_type of 'hour', 'minute' or 'second', return the SQL
        that truncates the given time or datetime field field_name to a time
        object with only the given specificity.

        If `tzname` is provided, the given value is truncated in a specific
        timezone.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseOperations may require a time_trunc_sql() method"
        )