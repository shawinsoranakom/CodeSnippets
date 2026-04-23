def test_filter_annotation(self):
        books = Book.objects.annotate(is_book=Value(1)).filter(is_book=1)
        for book in books:
            self.assertEqual(book.is_book, 1)