def test_get_union(self):
        qs = Number.objects.filter(num=2)
        self.assertEqual(qs.union(qs).get().num, 2)