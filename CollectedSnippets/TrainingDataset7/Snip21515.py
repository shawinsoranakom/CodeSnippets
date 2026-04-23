def test_aggregates(self):
        self.assertEqual(repr(Avg("a")), "Avg(F(a))")
        self.assertEqual(repr(Count("a")), "Count(F(a))")
        self.assertEqual(repr(Count("*")), "Count('*')")
        self.assertEqual(repr(Max("a")), "Max(F(a))")
        self.assertEqual(repr(Min("a")), "Min(F(a))")
        self.assertEqual(repr(StdDev("a")), "StdDev(F(a), sample=False)")
        self.assertEqual(repr(Sum("a")), "Sum(F(a))")
        self.assertEqual(
            repr(Variance("a", sample=True)), "Variance(F(a), sample=True)"
        )