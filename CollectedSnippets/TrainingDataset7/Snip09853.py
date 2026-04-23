def set_time_zone_sql(self):
        return "SELECT set_config('TimeZone', %s, false)"