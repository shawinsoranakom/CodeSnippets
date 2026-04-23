def test_lookup_date_with_use_tz(self):
        d = datetime.date(2014, 3, 12)
        # The following is equivalent to UTC 2014-03-12 18:34:23.24000.
        dt1 = datetime.datetime(
            2014, 3, 12, 10, 22, 23, 240000, tzinfo=timezone.get_current_timezone()
        )
        # The following is equivalent to UTC 2014-03-13 05:34:23.24000.
        dt2 = datetime.datetime(
            2014, 3, 12, 21, 22, 23, 240000, tzinfo=timezone.get_current_timezone()
        )
        t = datetime.time(21, 22, 23, 240000)
        m1 = DateTimeModel.objects.create(d=d, dt=dt1, t=t)
        m2 = DateTimeModel.objects.create(d=d, dt=dt2, t=t)
        # In Vancouver, we expect both results.
        self.assertCountEqual(
            DateTimeModel.objects.filter(dt__date=d),
            [m1, m2],
        )
        with self.settings(TIME_ZONE="UTC"):
            # But in UTC, the __date only matches one of them.
            self.assertCountEqual(DateTimeModel.objects.filter(dt__date=d), [m1])