def test_naive_datetime(self):
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30)
        Event.objects.create(dt=dt)
        event = Event.objects.get()
        self.assertEqual(event.dt, dt)