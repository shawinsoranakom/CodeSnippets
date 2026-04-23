def test_ordering_subqueries(self):
        qs1 = Number.objects.order_by("num")[:2]
        qs2 = Number.objects.order_by("-num")[:2]
        self.assertNumbersEqual(qs1.union(qs2).order_by("-num")[:4], [9, 8, 1, 0])