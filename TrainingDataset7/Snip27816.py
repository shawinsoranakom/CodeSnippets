def test_lookup_date_without_use_tz(self):
        d = datetime.date(2014, 3, 12)
        dt1 = datetime.datetime(2014, 3, 12, 21, 22, 23, 240000)
        dt2 = datetime.datetime(2014, 3, 11, 21, 22, 23, 240000)
        t = datetime.time(21, 22, 23, 240000)
        m = DateTimeModel.objects.create(d=d, dt=dt1, t=t)
        # Other model with different datetime.
        DateTimeModel.objects.create(d=d, dt=dt2, t=t)
        self.assertEqual(m, DateTimeModel.objects.get(dt__date=d))