def test_union_with_select_related_and_first(self):
        e1 = ExtraInfo.objects.create(value=7, info="e1")
        a1 = Author.objects.create(name="a1", num=1, extra=e1)
        Author.objects.create(name="a2", num=3, extra=e1)
        base_qs = Author.objects.select_related("extra").order_by()
        qs1 = base_qs.filter(name="a1")
        qs2 = base_qs.filter(name="a2")
        self.assertEqual(qs1.union(qs2).order_by("name").first(), a1)