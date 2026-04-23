def test_aware_datetime_in_utc(self):
        dt = datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC)
        Event.objects.create(dt=dt)
        event = Event.objects.get()
        self.assertIsNone(event.dt.tzinfo)
        # interpret the naive datetime in local time to get the correct value
        self.assertEqual(event.dt.replace(tzinfo=EAT), dt)