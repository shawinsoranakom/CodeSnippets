def test_union_with_first(self):
        e1 = ExtraInfo.objects.create(value=7, info="e1")
        a1 = Author.objects.create(name="a1", num=1, extra=e1)
        base_qs = Author.objects.order_by()
        qs1 = base_qs.filter(name="a1")
        qs2 = base_qs.filter(name="a2")
        self.assertEqual(qs1.union(qs2).first(), a1)