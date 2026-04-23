def test_connect_pool_with_timezone(self):
        new_time_zone = "Africa/Nairobi"
        new_connection = no_pool_connection(alias="default_pool")

        try:
            with new_connection.cursor() as cursor:
                cursor.execute("SHOW TIMEZONE")
                tz = cursor.fetchone()[0]
                self.assertNotEqual(new_time_zone, tz)
        finally:
            new_connection.close()

        del new_connection.timezone_name
        new_connection.settings_dict["OPTIONS"]["pool"] = True
        try:
            with self.settings(TIME_ZONE=new_time_zone):
                with new_connection.cursor() as cursor:
                    cursor.execute("SHOW TIMEZONE")
                    tz = cursor.fetchone()[0]
                    self.assertEqual(new_time_zone, tz)
        finally:
            new_connection.close()
            new_connection.close_pool()