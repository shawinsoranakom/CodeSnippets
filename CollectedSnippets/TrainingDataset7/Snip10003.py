def datetime_extract_sql(self, lookup_type, sql, params, tzname):
        return f"django_datetime_extract(%s, {sql}, %s, %s)", (
            lookup_type.lower(),
            *params,
            *self._convert_tznames_to_sql(tzname),
        )