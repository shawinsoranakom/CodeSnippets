def date_trunc_sql(self, lookup_type, sql, params, tzname=None):
        return f"django_date_trunc(%s, {sql}, %s, %s)", (
            lookup_type.lower(),
            *params,
            *self._convert_tznames_to_sql(tzname),
        )