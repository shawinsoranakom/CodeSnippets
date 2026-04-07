def date_extract_sql(self, lookup_type, sql, params):
        extract_sql = f"TO_CHAR({sql}, %s)"
        extract_param = None
        if lookup_type == "week_day":
            # TO_CHAR(field, 'D') returns an integer from 1-7, where 1=Sunday.
            extract_param = "D"
        elif lookup_type == "iso_week_day":
            extract_sql = f"TO_CHAR({sql} - 1, %s)"
            extract_param = "D"
        elif lookup_type == "week":
            # IW = ISO week number
            extract_param = "IW"
        elif lookup_type == "quarter":
            extract_param = "Q"
        elif lookup_type == "iso_year":
            extract_param = "IYYY"
        else:
            lookup_type = lookup_type.upper()
            if not self._extract_format_re.fullmatch(lookup_type):
                raise ValueError(f"Invalid loookup type: {lookup_type!r}")
            # https://docs.oracle.com/en/database/oracle/oracle-database/21/sqlrf/EXTRACT-datetime.html
            return f"EXTRACT({lookup_type} FROM {sql})", params
        return extract_sql, (*params, extract_param)