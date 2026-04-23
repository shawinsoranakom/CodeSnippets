def date_extract_sql(self, lookup_type, sql, params):
        # https://dev.mysql.com/doc/mysql/en/date-and-time-functions.html
        if lookup_type == "week_day":
            # DAYOFWEEK() returns an integer, 1-7, Sunday=1.
            return f"DAYOFWEEK({sql})", params
        elif lookup_type == "iso_week_day":
            # WEEKDAY() returns an integer, 0-6, Monday=0.
            return f"WEEKDAY({sql}) + 1", params
        elif lookup_type == "week":
            # Override the value of default_week_format for consistency with
            # other database backends.
            # Mode 3: Monday, 1-53, with 4 or more days this year.
            return f"WEEK({sql}, 3)", params
        elif lookup_type == "iso_year":
            # Get the year part from the YEARWEEK function, which returns a
            # number as year * 100 + week.
            return f"TRUNCATE(YEARWEEK({sql}, 3), -2) / 100", params
        else:
            # EXTRACT returns 1-53 based on ISO-8601 for the week number.
            lookup_type = lookup_type.upper()
            if not self._extract_format_re.fullmatch(lookup_type):
                raise ValueError(f"Invalid loookup type: {lookup_type!r}")
            return f"EXTRACT({lookup_type} FROM {sql})", params