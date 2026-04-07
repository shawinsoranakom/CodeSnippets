def datetime_trunc_sql(self, lookup_type, sql, params, tzname):
        """
        Given a lookup_type of 'year', 'month', 'day', 'hour', 'minute', or
        'second', return the SQL that truncates the given datetime field
        field_name to a datetime object with only the given specificity.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseOperations may require a datetime_trunc_sql() "
            "method"
        )