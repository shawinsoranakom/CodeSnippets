def test_cursor_explicit_time_zone(self):
        with override_database_connection_timezone("Europe/Paris"):
            with connection.cursor() as cursor:
                cursor.execute("SELECT CURRENT_TIMESTAMP")
                now = cursor.fetchone()[0]
                self.assertEqual(str(now.tzinfo), "Europe/Paris")