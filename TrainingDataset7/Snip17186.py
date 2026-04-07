def test_filter_annotation_with_double_f(self):
        books = Book.objects.annotate(other_rating=F("rating")).filter(
            other_rating=F("rating")
        )
        for book in books:
            self.assertEqual(book.other_rating, book.rating)