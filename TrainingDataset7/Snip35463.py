def test_aware_datetime_in_utc(self):
        dt = datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC)
        Event.objects.create(dt=dt)
        event = Event.objects.get()
        self.assertEqual(event.dt, dt)