def test_get_difference(self):
        qs1 = Number.objects.all()
        qs2 = Number.objects.exclude(num=2)
        self.assertEqual(qs1.difference(qs2).get().num, 2)