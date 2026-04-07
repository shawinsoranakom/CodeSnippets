def test_read_datetime(self):
        fake_dt = datetime.datetime(2011, 9, 1, 17, 20, 30, tzinfo=UTC)
        Event.objects.create(dt=fake_dt)

        with override_database_connection_timezone("Asia/Bangkok"):
            event = Event.objects.get()
            dt = datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC)
        self.assertEqual(event.dt, dt)