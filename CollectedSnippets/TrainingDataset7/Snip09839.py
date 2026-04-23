def _convert_sql_to_tz(self, sql, params, tzname):
        if tzname and settings.USE_TZ:
            tzname_param = self._prepare_tzname_delta(tzname)
            return f"{sql} AT TIME ZONE %s", (*params, tzname_param)
        return sql, params