def test_limits(self):
        qs1 = Number.objects.all()
        qs2 = Number.objects.all()
        self.assertEqual(len(list(qs1.union(qs2)[:2])), 2)