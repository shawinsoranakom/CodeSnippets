def datetime_cast_time_sql(self, sql, params, tzname):
        """
        Return the SQL to cast a datetime value to time value.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseOperations may require a "
            "datetime_cast_time_sql() method"
        )