def test_ordering_by_f_expression_and_alias(self):
        qs1 = Number.objects.filter(num__lte=1).values(alias=F("other_num"))
        qs2 = Number.objects.filter(num__gte=2, num__lte=3).values(alias=F("other_num"))
        self.assertQuerySetEqual(
            qs1.union(qs2).order_by(F("alias").desc()),
            [10, 9, 8, 7],
            operator.itemgetter("alias"),
        )
        Number.objects.create(num=-1)
        self.assertQuerySetEqual(
            qs1.union(qs2).order_by(F("alias").desc(nulls_last=True)),
            [10, 9, 8, 7, None],
            operator.itemgetter("alias"),
        )