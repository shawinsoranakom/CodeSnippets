def test_basic_f_annotation(self):
        books = Book.objects.annotate(another_rating=F("rating"))
        for book in books:
            self.assertEqual(book.another_rating, book.rating)