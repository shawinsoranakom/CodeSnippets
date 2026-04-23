def test_count_intersection(self):
        qs1 = Number.objects.filter(num__gte=5)
        qs2 = Number.objects.filter(num__lte=5)
        self.assertEqual(qs1.intersection(qs2).count(), 1)