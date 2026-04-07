def datetime_trunc_sql(self, lookup_type, sql, params, tzname):
        sql, params = self._convert_sql_to_tz(sql, params, tzname)
        fields = ["year", "month", "day", "hour", "minute", "second"]
        format = ("%Y-", "%m", "-%d", " %H:", "%i", ":%s")
        format_def = ("0000-", "01", "-01", " 00:", "00", ":00")
        if lookup_type == "quarter":
            return (
                f"CAST(DATE_FORMAT(MAKEDATE(YEAR({sql}), 1) + "
                f"INTERVAL QUARTER({sql}) QUARTER - "
                f"INTERVAL 1 QUARTER, %s) AS DATETIME)"
            ), (*params, *params, "%Y-%m-01 00:00:00")
        if lookup_type == "week":
            return (
                f"CAST(DATE_FORMAT("
                f"DATE_SUB({sql}, INTERVAL WEEKDAY({sql}) DAY), %s) AS DATETIME)"
            ), (*params, *params, "%Y-%m-%d 00:00:00")
        try:
            i = fields.index(lookup_type) + 1
        except ValueError:
            pass
        else:
            format_str = "".join(format[:i] + format_def[i:])
            return f"CAST(DATE_FORMAT({sql}, %s) AS DATETIME)", (*params, format_str)
        return sql, params