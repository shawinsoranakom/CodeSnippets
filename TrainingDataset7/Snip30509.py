def test_union_in_subquery(self):
        ReservedName.objects.bulk_create(
            [
                ReservedName(name="rn1", order=8),
                ReservedName(name="rn2", order=1),
                ReservedName(name="rn3", order=5),
            ]
        )
        qs1 = Number.objects.filter(num__gt=7, num=OuterRef("order"))
        qs2 = Number.objects.filter(num__lt=2, num=OuterRef("order"))
        self.assertCountEqual(
            ReservedName.objects.annotate(
                number=Subquery(qs1.union(qs2).values("num")),
            )
            .filter(number__isnull=False)
            .values_list("order", flat=True),
            [8, 1],
        )