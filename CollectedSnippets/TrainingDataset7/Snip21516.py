def test_distinct_aggregates(self):
        self.assertEqual(repr(Count("a", distinct=True)), "Count(F(a), distinct=True)")
        self.assertEqual(repr(Count("*", distinct=True)), "Count('*', distinct=True)")