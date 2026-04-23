def test_raw_sql(self):
        # Regression test for #17755
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT)
        event = Event.objects.create(dt=dt)
        self.assertSequenceEqual(
            list(
                Event.objects.raw("SELECT * FROM timezones_event WHERE dt = %s", [dt])
            ),
            [event],
        )