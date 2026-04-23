def test_filtered_aggregates(self):
        filter = Q(a=1)
        self.assertEqual(
            repr(Avg("a", filter=filter)), "Avg(F(a), filter=(AND: ('a', 1)))"
        )
        self.assertEqual(
            repr(Count("a", filter=filter)), "Count(F(a), filter=(AND: ('a', 1)))"
        )
        self.assertEqual(
            repr(Max("a", filter=filter)), "Max(F(a), filter=(AND: ('a', 1)))"
        )
        self.assertEqual(
            repr(Min("a", filter=filter)), "Min(F(a), filter=(AND: ('a', 1)))"
        )
        self.assertEqual(
            repr(StdDev("a", filter=filter)),
            "StdDev(F(a), filter=(AND: ('a', 1)), sample=False)",
        )
        self.assertEqual(
            repr(Sum("a", filter=filter)), "Sum(F(a), filter=(AND: ('a', 1)))"
        )
        self.assertEqual(
            repr(Variance("a", sample=True, filter=filter)),
            "Variance(F(a), filter=(AND: ('a', 1)), sample=True)",
        )
        self.assertEqual(
            repr(Count("a", filter=filter, distinct=True)),
            "Count(F(a), distinct=True, filter=(AND: ('a', 1)))",
        )