def test_union_with_field_and_annotation_values(self):
        qs1 = (
            Number.objects.filter(num=1)
            .annotate(
                zero=Value(0, IntegerField()),
            )
            .values_list("num", "zero")
        )
        qs2 = (
            Number.objects.filter(num=2)
            .annotate(
                zero=Value(0, IntegerField()),
            )
            .values_list("zero", "num")
        )
        self.assertCountEqual(qs1.union(qs2), [(1, 0), (0, 2)])