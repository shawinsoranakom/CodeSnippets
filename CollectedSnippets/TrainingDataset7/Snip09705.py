def date_trunc_sql(self, lookup_type, sql, params, tzname=None):
        sql, params = self._convert_sql_to_tz(sql, params, tzname)
        # https://docs.oracle.com/en/database/oracle/oracle-database/21/sqlrf/ROUND-and-TRUNC-Date-Functions.html
        trunc_param = None
        if lookup_type in ("year", "month"):
            trunc_param = lookup_type.upper()
        elif lookup_type == "quarter":
            trunc_param = "Q"
        elif lookup_type == "week":
            trunc_param = "IW"
        else:
            return f"TRUNC({sql})", params
        return f"TRUNC({sql}, %s)", (*params, trunc_param)