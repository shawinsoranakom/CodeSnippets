def test_aware_datetime_unsupported(self):
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT)
        msg = "backend does not support timezone-aware datetimes when USE_TZ is False."
        with self.assertRaisesMessage(ValueError, msg):
            Event.objects.create(dt=dt)