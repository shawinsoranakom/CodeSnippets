def test_stages(self):
        numbers = Number.objects.all()
        self.assertSequenceEqual(
            numbers.filter(num__gte=0) ^ numbers.filter(num__lte=11),
            [],
        )
        self.assertSequenceEqual(
            numbers.filter(num__gt=0) ^ numbers.filter(num__lt=11),
            [self.numbers[0]],
        )