def test_filter_agg_with_double_f(self):
        books = Book.objects.annotate(sum_rating=Sum("rating")).filter(
            sum_rating=F("sum_rating")
        )
        for book in books:
            self.assertEqual(book.sum_rating, book.rating)