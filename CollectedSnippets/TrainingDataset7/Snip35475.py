def test_query_datetimes_in_other_timezone(self):
        Event.objects.create(dt=datetime.datetime(2011, 1, 1, 1, 30, 0, tzinfo=EAT))
        Event.objects.create(dt=datetime.datetime(2011, 1, 1, 4, 30, 0, tzinfo=EAT))
        with timezone.override(UTC):
            self.assertSequenceEqual(
                Event.objects.datetimes("dt", "year"),
                [
                    datetime.datetime(2010, 1, 1, 0, 0, 0, tzinfo=UTC),
                    datetime.datetime(2011, 1, 1, 0, 0, 0, tzinfo=UTC),
                ],
            )
            self.assertSequenceEqual(
                Event.objects.datetimes("dt", "month"),
                [
                    datetime.datetime(2010, 12, 1, 0, 0, 0, tzinfo=UTC),
                    datetime.datetime(2011, 1, 1, 0, 0, 0, tzinfo=UTC),
                ],
            )
            self.assertSequenceEqual(
                Event.objects.datetimes("dt", "day"),
                [
                    datetime.datetime(2010, 12, 31, 0, 0, 0, tzinfo=UTC),
                    datetime.datetime(2011, 1, 1, 0, 0, 0, tzinfo=UTC),
                ],
            )
            self.assertSequenceEqual(
                Event.objects.datetimes("dt", "hour"),
                [
                    datetime.datetime(2010, 12, 31, 22, 0, 0, tzinfo=UTC),
                    datetime.datetime(2011, 1, 1, 1, 0, 0, tzinfo=UTC),
                ],
            )
            self.assertSequenceEqual(
                Event.objects.datetimes("dt", "minute"),
                [
                    datetime.datetime(2010, 12, 31, 22, 30, 0, tzinfo=UTC),
                    datetime.datetime(2011, 1, 1, 1, 30, 0, tzinfo=UTC),
                ],
            )
            self.assertSequenceEqual(
                Event.objects.datetimes("dt", "second"),
                [
                    datetime.datetime(2010, 12, 31, 22, 30, 0, tzinfo=UTC),
                    datetime.datetime(2011, 1, 1, 1, 30, 0, tzinfo=UTC),
                ],
            )