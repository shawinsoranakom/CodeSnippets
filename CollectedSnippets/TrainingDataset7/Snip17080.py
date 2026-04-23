def test_aggregate_annotation(self):
        # Aggregates can be composed over annotations.
        # The return type is derived from the composed aggregate
        vals = Book.objects.annotate(num_authors=Count("authors__id")).aggregate(
            Max("pages"), Max("price"), Sum("num_authors"), Avg("num_authors")
        )
        self.assertEqual(
            vals,
            {
                "num_authors__sum": 10,
                "num_authors__avg": Approximate(1.666, places=2),
                "pages__max": 1132,
                "price__max": Decimal("82.80"),
            },
        )

        # Regression for #15624 - Missing SELECT columns when using values,
        # annotate and aggregate in a single query
        self.assertEqual(
            Book.objects.annotate(c=Count("authors")).values("c").aggregate(Max("c")),
            {"c__max": 3},
        )