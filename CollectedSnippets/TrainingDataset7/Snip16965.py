def test_values_aggregation(self):
        # Refs #20782
        max_rating = Book.objects.values("rating").aggregate(max_rating=Max("rating"))
        self.assertEqual(max_rating["max_rating"], 5)
        max_books_per_rating = (
            Book.objects.values("rating")
            .annotate(books_per_rating=Count("id"))
            .aggregate(Max("books_per_rating"))
        )
        self.assertEqual(max_books_per_rating, {"books_per_rating__max": 3})