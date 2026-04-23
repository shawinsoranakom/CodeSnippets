def test_ticket12239(self):
        # Custom lookups are registered to round float values correctly on gte
        # and lt IntegerField queries.
        self.assertSequenceEqual(
            Number.objects.filter(num__gt=11.9),
            [self.num12],
        )
        self.assertSequenceEqual(Number.objects.filter(num__gt=12), [])
        self.assertSequenceEqual(Number.objects.filter(num__gt=12.0), [])
        self.assertSequenceEqual(Number.objects.filter(num__gt=12.1), [])
        self.assertCountEqual(
            Number.objects.filter(num__lt=12),
            [self.num4, self.num8],
        )
        self.assertCountEqual(
            Number.objects.filter(num__lt=12.0),
            [self.num4, self.num8],
        )
        self.assertCountEqual(
            Number.objects.filter(num__lt=12.1),
            [self.num4, self.num8, self.num12],
        )
        self.assertCountEqual(
            Number.objects.filter(num__gte=11.9),
            [self.num12],
        )
        self.assertCountEqual(
            Number.objects.filter(num__gte=12),
            [self.num12],
        )
        self.assertCountEqual(
            Number.objects.filter(num__gte=12.0),
            [self.num12],
        )
        self.assertSequenceEqual(Number.objects.filter(num__gte=12.1), [])
        self.assertSequenceEqual(Number.objects.filter(num__gte=12.9), [])
        self.assertCountEqual(
            Number.objects.filter(num__lte=11.9),
            [self.num4, self.num8],
        )
        self.assertCountEqual(
            Number.objects.filter(num__lte=12),
            [self.num4, self.num8, self.num12],
        )
        self.assertCountEqual(
            Number.objects.filter(num__lte=12.0),
            [self.num4, self.num8, self.num12],
        )
        self.assertCountEqual(
            Number.objects.filter(num__lte=12.1),
            [self.num4, self.num8, self.num12],
        )
        self.assertCountEqual(
            Number.objects.filter(num__lte=12.9),
            [self.num4, self.num8, self.num12],
        )