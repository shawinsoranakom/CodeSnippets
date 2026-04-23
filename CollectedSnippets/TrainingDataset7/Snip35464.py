def test_aware_datetime_in_other_timezone(self):
        dt = datetime.datetime(2011, 9, 1, 17, 20, 30, tzinfo=ICT)
        Event.objects.create(dt=dt)
        event = Event.objects.get()
        self.assertEqual(event.dt, dt)