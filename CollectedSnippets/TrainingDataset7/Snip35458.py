def test_datetime_from_date(self):
        dt = datetime.date(2011, 9, 1)
        with self.assertWarnsMessage(RuntimeWarning, self.naive_warning):
            Event.objects.create(dt=dt)
        event = Event.objects.get()
        self.assertEqual(event.dt, datetime.datetime(2011, 9, 1, tzinfo=EAT))