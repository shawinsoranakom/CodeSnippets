def set_time_zone_sql(self):
        """
        Return the SQL that will set the connection's time zone.

        Return '' if the backend doesn't support time zones.
        """
        return ""