def test_union_with_two_annotated_values_list(self):
        qs1 = (
            Number.objects.filter(num=1)
            .annotate(
                count=Value(0, IntegerField()),
            )
            .values_list("num", "count")
        )
        qs2 = (
            Number.objects.filter(num=2)
            .values("pk")
            .annotate(
                count=F("num"),
            )
            .annotate(
                num=Value(1, IntegerField()),
            )
            .values_list("num", "count")
        )
        self.assertCountEqual(qs1.union(qs2), [(1, 0), (1, 2)])