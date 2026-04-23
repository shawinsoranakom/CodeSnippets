def test_union_combined_slice_compound_empty(self):
        qs1 = Number.objects.filter(num__lte=2)[:3]
        qs2 = Number.objects.none()
        qs3 = qs1.union(qs2)
        self.assertNumbersEqual(qs3.order_by("num")[2:3], [2])