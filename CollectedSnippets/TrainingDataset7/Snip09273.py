def date_trunc_sql(self, lookup_type, sql, params, tzname=None):
        """
        Given a lookup_type of 'year', 'month', or 'day', return the SQL that
        truncates the given date or datetime field field_name to a date object
        with only the given specificity.

        If `tzname` is provided, the given value is truncated in a specific
        timezone.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseOperations may require a date_trunc_sql() "
            "method."
        )