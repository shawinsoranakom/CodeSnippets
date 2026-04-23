def test_simple_intersection(self):
        qs1 = Number.objects.filter(num__lte=5)
        qs2 = Number.objects.filter(num__gte=5)
        qs3 = Number.objects.filter(num__gte=4, num__lte=6)
        self.assertNumbersEqual(qs1.intersection(qs2, qs3), [5], ordered=False)