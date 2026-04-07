def test_union_empty_slice(self):
        qs = Number.objects.union()
        self.assertNumbersEqual(qs[:1], [0])
        qs = Number.objects.union(all=True)
        self.assertNumbersEqual(qs[:1], [0])
        self.assertNumbersEqual(qs.order_by("num")[0:], list(range(0, 10)))