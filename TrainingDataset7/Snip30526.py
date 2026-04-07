def test_get_intersection(self):
        qs1 = Number.objects.all()
        qs2 = Number.objects.filter(num=2)
        self.assertEqual(qs1.intersection(qs2).get().num, 2)