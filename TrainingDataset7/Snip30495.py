def test_union_with_extra_and_values_list(self):
        qs1 = (
            Number.objects.filter(num=1)
            .extra(
                select={"count": 0},
            )
            .values_list("num", "count")
        )
        qs2 = Number.objects.filter(num=2).extra(select={"count": 1})
        self.assertCountEqual(qs1.union(qs2), [(1, 0), (2, 1)])