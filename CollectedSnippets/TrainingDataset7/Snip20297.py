def test_year_boundaries(self):
        """Year boundary tests (ticket #3689)"""
        Donut.objects.create(
            name="Date Test 2007",
            baked_date=datetime.datetime(year=2007, month=12, day=31),
            consumed_at=datetime.datetime(
                year=2007, month=12, day=31, hour=23, minute=59, second=59
            ),
        )
        Donut.objects.create(
            name="Date Test 2006",
            baked_date=datetime.datetime(year=2006, month=1, day=1),
            consumed_at=datetime.datetime(year=2006, month=1, day=1),
        )
        self.assertEqual(
            "Date Test 2007", Donut.objects.filter(baked_date__year=2007)[0].name
        )
        self.assertEqual(
            "Date Test 2006", Donut.objects.filter(baked_date__year=2006)[0].name
        )

        Donut.objects.create(
            name="Apple Fritter",
            consumed_at=datetime.datetime(
                year=2007, month=4, day=20, hour=16, minute=19, second=59
            ),
        )

        self.assertEqual(
            ["Apple Fritter", "Date Test 2007"],
            list(
                Donut.objects.filter(consumed_at__year=2007)
                .order_by("name")
                .values_list("name", flat=True)
            ),
        )
        self.assertEqual(0, Donut.objects.filter(consumed_at__year=2005).count())
        self.assertEqual(0, Donut.objects.filter(consumed_at__year=2008).count())