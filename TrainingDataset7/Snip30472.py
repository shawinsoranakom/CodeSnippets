def test_union_none_slice(self):
        qs1 = Number.objects.filter(num__lte=0)
        qs2 = Number.objects.none()
        qs3 = qs1.union(qs2)
        self.assertNumbersEqual(qs3[:1], [0])