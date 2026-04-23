def test_order_by_in_subquery(self):
        aggregate = StringAgg(
            "authors__name",
            delimiter=Value(";"),
            order_by="authors__name",
        )
        subquery = (
            Book.objects.filter(
                pk=OuterRef("pk"),
            )
            .annotate(agg=aggregate)
            .values("agg")
        )
        values = list(
            Book.objects.annotate(
                agg=Subquery(subquery),
            )
            .order_by("agg")
            .values_list("agg", flat=True)
        )

        expected_values = [
            "Adrian Holovaty;Jacob Kaplan-Moss",
            "Brad Dayley",
            "James Bennett",
            "Jeffrey Forcier;Paul Bissex;Wesley J. Chun",
            "Peter Norvig",
            "Peter Norvig;Stuart Russell",
        ]

        self.assertEqual(expected_values, values)