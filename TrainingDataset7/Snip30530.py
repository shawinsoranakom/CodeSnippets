def test_combining_multiple_models(self):
        ReservedName.objects.create(name="99 little bugs", order=99)
        qs1 = Number.objects.filter(num=1).values_list("num", flat=True)
        qs2 = ReservedName.objects.values_list("order")
        self.assertEqual(list(qs1.union(qs2).order_by("num")), [1, 99])