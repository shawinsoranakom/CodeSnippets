def test_union_with_values_list_and_order_on_annotation(self):
        qs1 = Number.objects.annotate(
            annotation=Value(-1),
            multiplier=F("annotation"),
        ).filter(num__gte=6)
        qs2 = Number.objects.annotate(
            annotation=Value(2),
            multiplier=F("annotation"),
        ).filter(num__lte=5)
        self.assertSequenceEqual(
            qs1.union(qs2).order_by("annotation", "num").values_list("num", flat=True),
            [6, 7, 8, 9, 0, 1, 2, 3, 4, 5],
        )
        self.assertQuerySetEqual(
            qs1.union(qs2)
            .order_by(
                F("annotation") * F("multiplier"),
                "num",
            )
            .values("num"),
            [6, 7, 8, 9, 0, 1, 2, 3, 4, 5],
            operator.itemgetter("num"),
        )