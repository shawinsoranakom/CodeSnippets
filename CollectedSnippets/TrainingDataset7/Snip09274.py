def datetime_cast_date_sql(self, sql, params, tzname):
        """
        Return the SQL to cast a datetime value to date value.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseOperations may require a "
            "datetime_cast_date_sql() method."
        )