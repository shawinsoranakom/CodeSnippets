def test_write_datetime(self):
        dt = datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC)
        with override_database_connection_timezone("Asia/Bangkok"):
            Event.objects.create(dt=dt)

        event = Event.objects.get()
        fake_dt = datetime.datetime(2011, 9, 1, 17, 20, 30, tzinfo=UTC)
        self.assertEqual(event.dt, fake_dt)