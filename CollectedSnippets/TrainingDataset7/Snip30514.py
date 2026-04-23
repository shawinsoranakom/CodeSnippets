def test_count_union(self):
        qs1 = Number.objects.filter(num__lte=1).values("num")
        qs2 = Number.objects.filter(num__gte=2, num__lte=3).values("num")
        self.assertEqual(qs1.union(qs2).count(), 4)