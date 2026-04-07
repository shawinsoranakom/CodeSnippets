def test_count_union_with_select_related_in_values(self):
        e1 = ExtraInfo.objects.create(value=1, info="e1")
        a1 = Author.objects.create(name="a1", num=1, extra=e1)
        qs = Author.objects.select_related("extra").values("pk", "name", "extra__value")
        self.assertCountEqual(
            qs.union(qs), [{"pk": a1.id, "name": "a1", "extra__value": 1}]
        )