def test_conditional_aggregate(self):
        # Conditional aggregation of a grouped queryset.
        self.assertEqual(
            Book.objects.annotate(c=Count("authors"))
            .values("pk")
            .aggregate(test=Sum(Case(When(c__gt=1, then=1))))["test"],
            3,
        )