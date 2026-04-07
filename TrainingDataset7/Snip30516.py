def test_count_union_with_select_related(self):
        e1 = ExtraInfo.objects.create(value=1, info="e1")
        Author.objects.create(name="a1", num=1, extra=e1)
        qs = Author.objects.select_related("extra").order_by()
        self.assertEqual(qs.union(qs).count(), 1)