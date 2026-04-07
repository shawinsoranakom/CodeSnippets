def test_filtered_aggregate_full_condition(self):
        book = Book.objects.annotate(
            authors_count=Count(
                "authors",
                filter=~Q(authors__in=[]),
            ),
        ).get(pk=self.b1.pk)
        self.assertEqual(book.authors_count, 2)
        aggregate = Book.objects.aggregate(
            max_rating=Max("rating", filter=~Q(rating__in=[]))
        )
        self.assertEqual(aggregate, {"max_rating": 4.5})