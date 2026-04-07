def _convert_tznames_to_sql(self, tzname):
        if tzname and settings.USE_TZ:
            return tzname, self.connection.timezone_name
        return None, None