def test_naive_datetime_with_microsecond(self):
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30, 405060)
        with self.assertWarnsMessage(RuntimeWarning, self.naive_warning):
            Event.objects.create(dt=dt)
        event = Event.objects.get()
        # naive datetimes are interpreted in local time
        self.assertEqual(event.dt, dt.replace(tzinfo=EAT))