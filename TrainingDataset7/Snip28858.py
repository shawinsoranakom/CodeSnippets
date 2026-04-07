def test_date_filter_null(self):
        # Date filtering was failing with NULL date values in SQLite
        # (regression test for #3501, among other things).
        Party.objects.create(when=datetime.datetime(1999, 1, 1))
        Party.objects.create()
        p = Party.objects.filter(when__month=1)[0]
        self.assertEqual(p.when, datetime.date(1999, 1, 1))
        self.assertQuerySetEqual(
            Party.objects.filter(pk=p.pk).dates("when", "month"),
            [1],
            attrgetter("month"),
        )