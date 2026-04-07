def date_trunc_sql(self, lookup_type, sql, params, tzname=None):
        sql, params = self._convert_sql_to_tz(sql, params, tzname)
        fields = {
            "year": "%Y-01-01",
            "month": "%Y-%m-01",
        }
        if lookup_type in fields:
            format_str = fields[lookup_type]
            return f"CAST(DATE_FORMAT({sql}, %s) AS DATE)", (*params, format_str)
        elif lookup_type == "quarter":
            return (
                f"MAKEDATE(YEAR({sql}), 1) + "
                f"INTERVAL QUARTER({sql}) QUARTER - INTERVAL 1 QUARTER",
                (*params, *params),
            )
        elif lookup_type == "week":
            return f"DATE_SUB({sql}, INTERVAL WEEKDAY({sql}) DAY)", (*params, *params)
        else:
            return f"DATE({sql})", params