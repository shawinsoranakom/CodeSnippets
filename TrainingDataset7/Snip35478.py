def test_cursor_execute_accepts_naive_datetime(self):
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT)
        utc_naive_dt = timezone.make_naive(dt, UTC)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO timezones_event (dt) VALUES (%s)", [utc_naive_dt]
            )
        event = Event.objects.get()
        self.assertEqual(event.dt, dt)