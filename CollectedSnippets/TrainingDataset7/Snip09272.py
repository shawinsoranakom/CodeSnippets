def date_extract_sql(self, lookup_type, sql, params):
        """
        Given a lookup_type of 'year', 'month', or 'day', return the SQL that
        extracts a value from the given date field field_name.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseOperations may require a date_extract_sql() "
            "method"
        )