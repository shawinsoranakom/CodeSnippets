def test_ordering_by_alias(self):
        qs1 = Number.objects.filter(num__lte=1).values(alias=F("num"))
        qs2 = Number.objects.filter(num__gte=2, num__lte=3).values(alias=F("num"))
        self.assertQuerySetEqual(
            qs1.union(qs2).order_by("-alias"),
            [3, 2, 1, 0],
            operator.itemgetter("alias"),
        )