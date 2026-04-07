def test_time_field(self):
        # Test for ticket #12059: TimeField wrongly handling datetime.datetime
        # object.
        d = Donut(name="Apple Fritter")
        d.baked_time = datetime.datetime(
            year=2007, month=4, day=20, hour=16, minute=19, second=59
        )
        d.save()

        d2 = Donut.objects.get(name="Apple Fritter")
        self.assertEqual(d2.baked_time, datetime.time(16, 19, 59))