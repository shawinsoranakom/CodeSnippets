def test_order_by_aggregate_default_alias(self):
        publisher_books = (
            Publisher.objects.values("book")
            .annotate(Count("book"))
            .order_by("book__count", "book__id")
            .values_list("book", flat=True)
        )
        self.assertQuerySetEqual(
            publisher_books,
            [
                None,
                self.b1.id,
                self.b2.id,
                self.b3.id,
                self.b4.id,
                self.b5.id,
                self.b6.id,
            ],
        )