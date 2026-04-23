def test_cursor_execute_accepts_naive_datetime(self):
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30)
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO timezones_event (dt) VALUES (%s)", [dt])
        event = Event.objects.get()
        self.assertEqual(event.dt, dt)