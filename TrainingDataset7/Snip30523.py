def test_exists_difference(self):
        qs1 = Number.objects.filter(num__gte=5)
        qs2 = Number.objects.filter(num__gte=3)
        self.assertIs(qs1.difference(qs2).exists(), False)
        self.assertIs(qs2.difference(qs1).exists(), True)