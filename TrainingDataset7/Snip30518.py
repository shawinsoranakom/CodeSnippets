def test_count_difference(self):
        qs1 = Number.objects.filter(num__lt=10)
        qs2 = Number.objects.filter(num__lt=9)
        self.assertEqual(qs1.difference(qs2).count(), 1)