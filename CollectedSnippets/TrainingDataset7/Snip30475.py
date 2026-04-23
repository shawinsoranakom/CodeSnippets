def test_union_empty_filter_slice(self):
        qs1 = Number.objects.filter(num__lte=0)
        qs2 = Number.objects.filter(pk__in=[])
        qs3 = qs1.union(qs2)
        self.assertNumbersEqual(qs3[:1], [0])