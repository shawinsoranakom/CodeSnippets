def test_multiple_aggregate_references(self):
        aggregates = Author.objects.aggregate(
            total_books=Count("book"),
            coalesced_total_books=Coalesce("total_books", 0),
        )
        self.assertEqual(
            aggregates,
            {
                "total_books": 10,
                "coalesced_total_books": 10,
            },
        )