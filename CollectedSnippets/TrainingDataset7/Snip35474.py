def test_query_datetimes(self):
        Event.objects.create(dt=datetime.datetime(2011, 1, 1, 1, 30, 0, tzinfo=EAT))
        Event.objects.create(dt=datetime.datetime(2011, 1, 1, 4, 30, 0, tzinfo=EAT))
        self.assertSequenceEqual(
            Event.objects.datetimes("dt", "year"),
            [datetime.datetime(2011, 1, 1, 0, 0, 0, tzinfo=EAT)],
        )
        self.assertSequenceEqual(
            Event.objects.datetimes("dt", "month"),
            [datetime.datetime(2011, 1, 1, 0, 0, 0, tzinfo=EAT)],
        )
        self.assertSequenceEqual(
            Event.objects.datetimes("dt", "day"),
            [datetime.datetime(2011, 1, 1, 0, 0, 0, tzinfo=EAT)],
        )
        self.assertSequenceEqual(
            Event.objects.datetimes("dt", "hour"),
            [
                datetime.datetime(2011, 1, 1, 1, 0, 0, tzinfo=EAT),
                datetime.datetime(2011, 1, 1, 4, 0, 0, tzinfo=EAT),
            ],
        )
        self.assertSequenceEqual(
            Event.objects.datetimes("dt", "minute"),
            [
                datetime.datetime(2011, 1, 1, 1, 30, 0, tzinfo=EAT),
                datetime.datetime(2011, 1, 1, 4, 30, 0, tzinfo=EAT),
            ],
        )
        self.assertSequenceEqual(
            Event.objects.datetimes("dt", "second"),
            [
                datetime.datetime(2011, 1, 1, 1, 30, 0, tzinfo=EAT),
                datetime.datetime(2011, 1, 1, 4, 30, 0, tzinfo=EAT),
            ],
        )