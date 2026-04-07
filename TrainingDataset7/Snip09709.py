def datetime_cast_time_sql(self, sql, params, tzname):
        # Since `TimeField` values are stored as TIMESTAMP change to the
        # default date and convert the field to the specified timezone.
        sql, params = self._convert_sql_to_tz(sql, params, tzname)
        convert_datetime_sql = (
            f"TO_TIMESTAMP(CONCAT('1900-01-01 ', TO_CHAR({sql}, 'HH24:MI:SS.FF')), "
            f"'YYYY-MM-DD HH24:MI:SS.FF')"
        )
        return (
            f"CASE WHEN {sql} IS NOT NULL THEN {convert_datetime_sql} ELSE NULL END",
            (*params, *params),
        )