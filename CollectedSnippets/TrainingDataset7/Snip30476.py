def test_union_slice_compound_empty(self):
        qs1 = Number.objects.filter(num__lte=0)[:1]
        qs2 = Number.objects.none()
        qs3 = qs1.union(qs2)
        self.assertNumbersEqual(qs3[:1], [0])