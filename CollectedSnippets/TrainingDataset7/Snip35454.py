def test_cursor_execute_returns_naive_datetime(self):
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30)
        Event.objects.create(dt=dt)
        with connection.cursor() as cursor:
            cursor.execute("SELECT dt FROM timezones_event WHERE dt = %s", [dt])
            self.assertEqual(cursor.fetchall()[0][0], dt)