def datetime_trunc_sql(self, lookup_type, sql, params, tzname):
        sql, params = self._convert_sql_to_tz(sql, params, tzname)
        # https://docs.oracle.com/en/database/oracle/oracle-database/21/sqlrf/ROUND-and-TRUNC-Date-Functions.html
        trunc_param = None
        if lookup_type in ("year", "month"):
            trunc_param = lookup_type.upper()
        elif lookup_type == "quarter":
            trunc_param = "Q"
        elif lookup_type == "week":
            trunc_param = "IW"
        elif lookup_type == "hour":
            trunc_param = "HH24"
        elif lookup_type == "minute":
            trunc_param = "MI"
        elif lookup_type == "day":
            return f"TRUNC({sql})", params
        else:
            # Cast to DATE removes sub-second precision.
            return f"CAST({sql} AS DATE)", params
        return f"TRUNC({sql}, %s)", (*params, trunc_param)