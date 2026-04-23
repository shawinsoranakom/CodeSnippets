def test_aggregate(self):
        # Ordering requests are ignored
        self.assertEqual(
            Author.objects.order_by("name").aggregate(Avg("age")),
            {"age__avg": Approximate(37.444, places=1)},
        )

        # Implicit ordering is also ignored
        self.assertEqual(
            Book.objects.aggregate(Sum("pages")),
            {"pages__sum": 3703},
        )

        # Baseline results
        self.assertEqual(
            Book.objects.aggregate(Sum("pages"), Avg("pages")),
            {"pages__sum": 3703, "pages__avg": Approximate(617.166, places=2)},
        )

        # Empty values query doesn't affect grouping or results
        self.assertEqual(
            Book.objects.values().aggregate(Sum("pages"), Avg("pages")),
            {"pages__sum": 3703, "pages__avg": Approximate(617.166, places=2)},
        )

        # Aggregate overrides extra selected column
        self.assertEqual(
            Book.objects.extra(select={"price_per_page": "price / pages"}).aggregate(
                Sum("pages")
            ),
            {"pages__sum": 3703},
        )