def test_qs_with_subcompound_qs(self):
        qs1 = Number.objects.all()
        qs2 = Number.objects.intersection(Number.objects.filter(num__gt=1))
        self.assertEqual(qs1.difference(qs2).count(), 2)