def datetime_cast_date_sql(self, sql, params, tzname):
        return f"django_datetime_cast_date({sql}, %s, %s)", (
            *params,
            *self._convert_tznames_to_sql(tzname),
        )