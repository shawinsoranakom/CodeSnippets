def datetime_cast_time_sql(self, sql, params, tzname):
        return f"django_datetime_cast_time({sql}, %s, %s)", (
            *params,
            *self._convert_tznames_to_sql(tzname),
        )