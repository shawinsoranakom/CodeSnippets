def test_union_order_with_null_first_last(self):
        Number.objects.filter(other_num=5).update(other_num=None)
        qs1 = Number.objects.filter(num__lte=1)
        qs2 = Number.objects.filter(num__gte=2)
        qs3 = qs1.union(qs2)
        self.assertSequenceEqual(
            qs3.order_by(
                F("other_num").asc(nulls_first=True),
            ).values_list("other_num", flat=True),
            [None, 1, 2, 3, 4, 6, 7, 8, 9, 10],
        )
        self.assertSequenceEqual(
            qs3.order_by(
                F("other_num").asc(nulls_last=True),
            ).values_list("other_num", flat=True),
            [1, 2, 3, 4, 6, 7, 8, 9, 10, None],
        )