def test_union_in_subquery_related_outerref(self):
        e1 = ExtraInfo.objects.create(value=7, info="e3")
        e2 = ExtraInfo.objects.create(value=5, info="e2")
        e3 = ExtraInfo.objects.create(value=1, info="e1")
        Author.objects.bulk_create(
            [
                Author(name="a1", num=1, extra=e1),
                Author(name="a2", num=3, extra=e2),
                Author(name="a3", num=2, extra=e3),
            ]
        )
        qs1 = ExtraInfo.objects.order_by().filter(value=OuterRef("num"))
        qs2 = ExtraInfo.objects.order_by().filter(value__lt=OuterRef("extra__value"))
        qs = (
            Author.objects.annotate(
                info=Subquery(qs1.union(qs2).values("info")[:1]),
            )
            .filter(info__isnull=False)
            .values_list("name", flat=True)
        )
        self.assertCountEqual(qs, ["a1", "a2"])
        # Combined queries don't mutate.
        self.assertCountEqual(qs, ["a1", "a2"])