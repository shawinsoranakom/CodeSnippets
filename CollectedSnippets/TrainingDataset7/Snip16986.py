def test_complex_values_aggregation(self):
        max_rating = Book.objects.values("rating").aggregate(
            double_max_rating=Max("rating") + Max("rating")
        )
        self.assertEqual(max_rating["double_max_rating"], 5 * 2)

        max_books_per_rating = (
            Book.objects.values("rating")
            .annotate(books_per_rating=Count("id") + 5)
            .aggregate(Max("books_per_rating"))
        )
        self.assertEqual(max_books_per_rating, {"books_per_rating__max": 3 + 5})