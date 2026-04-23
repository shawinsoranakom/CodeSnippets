def test_naive_datetime(self):
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30)
        with self.assertWarnsMessage(RuntimeWarning, self.naive_warning):
            Event.objects.create(dt=dt)
        event = Event.objects.get()
        # naive datetimes are interpreted in local time
        self.assertEqual(event.dt, dt.replace(tzinfo=EAT))