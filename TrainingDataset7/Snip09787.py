def _configure_timezone(self, connection):
        conn_timezone_name = connection.info.parameter_status("TimeZone")
        timezone_name = self.timezone_name
        if timezone_name and conn_timezone_name != timezone_name:
            with connection.cursor() as cursor:
                cursor.execute(self.ops.set_time_zone_sql(), [timezone_name])
            return True
        return False