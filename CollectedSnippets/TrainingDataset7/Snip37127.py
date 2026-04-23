def test_filter_negated(self):
        self.assertCountEqual(
            Number.objects.filter(Q(num__lte=7) ^ ~Q(num__lt=3)),
            self.numbers[:3] + self.numbers[8:],
        )
        self.assertCountEqual(
            Number.objects.filter(~Q(num__gt=7) ^ ~Q(num__lt=3)),
            self.numbers[:3] + self.numbers[8:],
        )
        self.assertCountEqual(
            Number.objects.filter(Q(num__lte=7) ^ ~Q(num__lt=3) ^ Q(num__lte=1)),
            [self.numbers[2]] + self.numbers[8:],
        )
        self.assertCountEqual(
            Number.objects.filter(~(Q(num__lte=7) ^ ~Q(num__lt=3) ^ Q(num__lte=1))),
            self.numbers[:2] + self.numbers[3:8],
        )