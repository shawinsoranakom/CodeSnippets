def test_date_type(self):
        d = Donut(name="Apple Fritter")
        d.baked_date = datetime.date(year=1938, month=6, day=4)
        d.baked_time = datetime.time(hour=5, minute=30)
        d.consumed_at = datetime.datetime(
            year=2007, month=4, day=20, hour=16, minute=19, second=59
        )
        d.save()

        d2 = Donut.objects.get(name="Apple Fritter")
        self.assertEqual(d2.baked_date, datetime.date(1938, 6, 4))
        self.assertEqual(d2.baked_time, datetime.time(5, 30))
        self.assertEqual(d2.consumed_at, datetime.datetime(2007, 4, 20, 16, 19, 59))