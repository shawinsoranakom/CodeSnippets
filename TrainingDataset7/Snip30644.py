def test_ticket4289(self):
        # A slight variation on the restricting the filtering choices by the
        # lookup constraints.
        self.assertSequenceEqual(Number.objects.filter(num__lt=4), [])
        self.assertSequenceEqual(Number.objects.filter(num__gt=8, num__lt=12), [])
        self.assertSequenceEqual(
            Number.objects.filter(num__gt=8, num__lt=13),
            [self.num12],
        )
        self.assertSequenceEqual(
            Number.objects.filter(Q(num__lt=4) | Q(num__gt=8, num__lt=12)), []
        )
        self.assertSequenceEqual(
            Number.objects.filter(Q(num__gt=8, num__lt=12) | Q(num__lt=4)), []
        )
        self.assertSequenceEqual(
            Number.objects.filter(Q(num__gt=8) & Q(num__lt=12) | Q(num__lt=4)), []
        )
        self.assertSequenceEqual(
            Number.objects.filter(Q(num__gt=7) & Q(num__lt=12) | Q(num__lt=4)),
            [self.num8],
        )