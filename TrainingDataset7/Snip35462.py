def test_aware_datetime_in_local_timezone_with_microsecond(self):
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30, 405060, tzinfo=EAT)
        Event.objects.create(dt=dt)
        event = Event.objects.get()
        self.assertEqual(event.dt, dt)