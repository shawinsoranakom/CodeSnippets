def _convert_sql_to_tz(self, sql, params, tzname):
        if not (settings.USE_TZ and tzname):
            return sql, params
        if not self._tzname_re.match(tzname):
            raise ValueError("Invalid time zone name: %s" % tzname)
        # Convert from connection timezone to the local time, returning
        # TIMESTAMP WITH TIME ZONE and cast it back to TIMESTAMP to strip the
        # TIME ZONE details.
        if self.connection.timezone_name != tzname:
            from_timezone_name = self.connection.timezone_name
            to_timezone_name = self._prepare_tzname_delta(tzname)
            return (
                f"CAST((FROM_TZ({sql}, '{from_timezone_name}') AT TIME ZONE "
                f"'{to_timezone_name}') AS TIMESTAMP)",
                params,
            )
        return sql, params