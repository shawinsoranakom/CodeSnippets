def test_filter_annotation_with_f(self):
        books = Book.objects.annotate(other_rating=F("rating")).filter(other_rating=3.5)
        for book in books:
            self.assertEqual(book.other_rating, 3.5)