def test_exists_intersection(self):
        qs1 = Number.objects.filter(num__gt=5)
        qs2 = Number.objects.filter(num__lt=5)
        self.assertIs(qs1.intersection(qs1).exists(), True)
        self.assertIs(qs1.intersection(qs2).exists(), False)