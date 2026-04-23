def time_trunc_sql(self, lookup_type, sql, params, tzname=None):
        sql, params = self._convert_sql_to_tz(sql, params, tzname)
        fields = {
            "hour": "%H:00:00",
            "minute": "%H:%i:00",
            "second": "%H:%i:%s",
        }
        if lookup_type in fields:
            format_str = fields[lookup_type]
            return f"CAST(DATE_FORMAT({sql}, %s) AS TIME)", (*params, format_str)
        else:
            return f"TIME({sql})", params