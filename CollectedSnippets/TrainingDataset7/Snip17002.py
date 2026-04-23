def test_any_value_aggregate_clause(self):
        books_qs = (
            Book.objects.values(greatest_pages=Greatest("pages", 600))
            .annotate(
                num_authors=Count("authors"),
                pages_per_author=(
                    AnyValue("greatest_pages") / (Cast("num_authors", FloatField()))
                ),
            )
            .values_list("pages_per_author", flat=True)
            .order_by("pages_per_author")
        )
        self.assertAlmostEqual(books_qs[0], 600 / 7, places=4)
        self.assertAlmostEqual(books_qs[1], 1132 / 2, places=4)
        self.assertAlmostEqual(books_qs[2], 946 / 1, places=4)

        aggregate_qs = books_qs.aggregate(Avg("pages_per_author"))
        self.assertAlmostEqual(
            aggregate_qs["pages_per_author__avg"],
            ((600 / 7) + (1132 / 2) + (946 / 1)) / 3,
            places=4,
        )