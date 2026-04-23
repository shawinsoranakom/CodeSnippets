def test_ticket10742(self):
        # Queries used in an __in clause don't execute subqueries

        subq = Author.objects.filter(num__lt=3000)
        qs = Author.objects.filter(pk__in=subq)
        self.assertSequenceEqual(qs, [self.a1, self.a2])

        # The subquery result cache should not be populated
        self.assertIsNone(subq._result_cache)

        subq = Author.objects.filter(num__lt=3000)
        qs = Author.objects.exclude(pk__in=subq)
        self.assertSequenceEqual(qs, [self.a3, self.a4])

        # The subquery result cache should not be populated
        self.assertIsNone(subq._result_cache)

        subq = Author.objects.filter(num__lt=3000)
        self.assertSequenceEqual(
            Author.objects.filter(Q(pk__in=subq) & Q(name="a1")),
            [self.a1],
        )

        # The subquery result cache should not be populated
        self.assertIsNone(subq._result_cache)