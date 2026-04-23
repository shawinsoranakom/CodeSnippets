def test_date_lookup(self):
        # Regression test for #659
        Party.objects.create(when=datetime.datetime(1999, 12, 31))
        Party.objects.create(when=datetime.datetime(1998, 12, 31))
        Party.objects.create(when=datetime.datetime(1999, 1, 1))
        Party.objects.create(when=datetime.datetime(1, 3, 3))
        self.assertQuerySetEqual(Party.objects.filter(when__month=2), [])
        self.assertQuerySetEqual(
            Party.objects.filter(when__month=1),
            [datetime.date(1999, 1, 1)],
            attrgetter("when"),
        )
        self.assertQuerySetEqual(
            Party.objects.filter(when__month=12),
            [
                datetime.date(1999, 12, 31),
                datetime.date(1998, 12, 31),
            ],
            attrgetter("when"),
            ordered=False,
        )
        self.assertQuerySetEqual(
            Party.objects.filter(when__year=1998),
            [
                datetime.date(1998, 12, 31),
            ],
            attrgetter("when"),
        )
        # Regression test for #8510
        self.assertQuerySetEqual(
            Party.objects.filter(when__day="31"),
            [
                datetime.date(1999, 12, 31),
                datetime.date(1998, 12, 31),
            ],
            attrgetter("when"),
            ordered=False,
        )
        self.assertQuerySetEqual(
            Party.objects.filter(when__month="12"),
            [
                datetime.date(1999, 12, 31),
                datetime.date(1998, 12, 31),
            ],
            attrgetter("when"),
            ordered=False,
        )
        self.assertQuerySetEqual(
            Party.objects.filter(when__year="1998"),
            [
                datetime.date(1998, 12, 31),
            ],
            attrgetter("when"),
        )

        # Regression test for #18969
        self.assertQuerySetEqual(
            Party.objects.filter(when__year=1),
            [
                datetime.date(1, 3, 3),
            ],
            attrgetter("when"),
        )
        self.assertQuerySetEqual(
            Party.objects.filter(when__year="1"),
            [
                datetime.date(1, 3, 3),
            ],
            attrgetter("when"),
        )